"""
Service Deepgram pour la transcription audio
Utilise l'API Deepgram pour convertir les fichiers audio en texte
"""

import os
import json
import logging
import mimetypes
import tempfile
import requests
from django.conf import settings
from decouple import config

logger = logging.getLogger(__name__)

class DeepgramService:
    """Service pour la transcription audio via Deepgram API"""

    # Configuration retenue après diagnostic (tâche 33).
    #
    # Mesures sur les deux audios de test (même cours, 391 s et 403 s) :
    #   nova-2 + language='fr'    -> 56 % de l'audio couvert (arrêt à 220 s
    #                                sur 391 s dès que des voix parasites
    #                                couvrent la scène), texte interrompu en
    #                                pleine phrase ;
    #   nova-3 + language='fr'    -> 70 % ;
    #   nova-3 + language='multi' -> 99,5 %, texte complet jusqu'à la
    #                                dernière phrase du cours.
    #
    # Le mode 'multi' de nova-3 transcrit les passages bruyants ou plusieurs
    # locuteurs se superposent, que le modèle français mono-langue
    # abandonnait sans le signaler. Il n'est PAS supporté par nova-2
    # (qui renvoie une transcription vide).
    MODEL = 'nova-3'
    DEFAULT_LANGUAGE = 'multi'

    # En dessous de ce taux de couverture, la transcription est considérée
    # comme incomplète : on le signale au lieu de générer un résumé tronqué
    # en silence (c'est ce qui masquait le problème initialement).
    SEUIL_COUVERTURE = 90.0

    # Bornes du timeout de l'appel HTTP à Deepgram. Elles sont calibrées sur
    # la DURÉE de l'audio, jamais sur la taille du fichier : un cours de 3 h
    # en AMR ne pèse que ~17 Mo, donc l'ancienne formule (5 min + 2 min par
    # tranche de 50 Mo) restait bloquée à 5 min et pouvait couper un long
    # cours en pleine transcription.
    TIMEOUT_MIN = 300               # plancher : 5 min
    TIMEOUT_MAX = 1800              # plafond : 30 min (< soft_time_limit Celery 3300 s)
    TIMEOUT_PAR_MINUTE_AUDIO = 6    # secondes accordées par minute d'audio

    # ── Récupération des passages perdus (tâche 36) ─────────────────────────
    #
    # Cause mesurée : même avec la bonne configuration, un appel sur le fichier
    # ENTIER laisse des passages sans aucun mot, alors que les mêmes passages
    # transcrits SEULS produisent du texte. Mesures sur les audios de test :
    #   bruité, 358,1 s → 374,5 s : 0 mot en entier  ->  26 mots en segment
    #   clair , 286,7 s → 302,1 s : 0 mot en entier  ->  37 mots en segment
    #   bruité, 220,0 s → 391,2 s : 0 mot en entier  -> 363 mots en segment
    # Le taux de couverture ne mesurait que la FIN du dernier mot : ces trous
    # internes restaient donc totalement invisibles (99,9 % affichés alors que
    # 50 s de cours manquaient).
    #
    # Ces passages sont donc re-transcrits isolément, puis recollés à leur
    # position réelle. Aucun mot existant n'est retiré : la correction ne peut
    # qu'ajouter ce qui manquait.
    SEUIL_TROU = 10.0               # s : en dessous, c'est une respiration normale
    DUREE_MAX_RECUPERATION = 600.0  # s : plafond de ré-audio par fichier (coût borné)
    MAX_SEGMENTS = 12               # nb maximum de passages récupérés par fichier

    # Taille TOTALE d'une trame AMR-NB (en-tête d'un octet COMPRIS) selon son
    # mode. Un AMR est une suite de trames de 20 ms : le découper revient à
    # recopier des trames, donc sans ré-encodage ni perte.
    TAILLE_TRAME_AMR = (13, 14, 16, 18, 20, 21, 27, 32, 6, 0, 0, 0, 0, 0, 0, 1)
    DUREE_TRAME_AMR = 0.02

    def __init__(self):
        # Utiliser decouple pour lire depuis .env
        self.api_key = config('DEEPGRAM_API_KEY', default='')
        self.base_url = 'https://api.deepgram.com/v1/listen'
        
        if not self.api_key:
            logger.warning("⚠️ DEEPGRAM_API_KEY non configurée")
    
    def is_configured(self):
        """Vérifie si le service est correctement configuré"""
        return bool(self.api_key)

    def _duree_audio_fichier(self, file_path):
        """
        Durée du fichier en secondes lue via mutagen, ou None si illisible.

        mutagen couvre les formats de l'application (m4a, mp3, wav, ogg) mais
        pas l'AMR, très répandu chez les dictaphones : le repli sur la taille
        du fichier reste donc nécessaire.
        """
        try:
            from mutagen import File as MutagenFile
            info = MutagenFile(file_path)
            longueur = getattr(getattr(info, 'info', None), 'length', None)
            if longueur and longueur > 0:
                return float(longueur)
        except Exception as e:
            logger.debug(f"Durée illisible via mutagen ({file_path}): {e}")
        return None

    def _adaptive_timeout(self, file_path=None, size_bytes=None):
        """
        Calcule le timeout de l'appel Deepgram à partir de la DURÉE de l'audio.

        Se baser sur la taille du fichier était trompeur : les formats
        compressés restent sous 50 Mo même pour 3 h d'enregistrement, si bien
        que le timeout ne dépassait jamais 5 min. On estime donc la durée
        (mutagen, puis repli volontairement pessimiste sur la taille) et on
        accorde TIMEOUT_PAR_MINUTE_AUDIO secondes par minute d'audio, entre
        TIMEOUT_MIN et TIMEOUT_MAX.
        """
        duree = self._duree_audio_fichier(file_path) if file_path else None

        if not duree and size_bytes:
            # 500 octets/seconde : débit plancher des formats compressés.
            # On préfère surestimer la durée — donc le timeout — que l'inverse.
            duree = size_bytes / 500.0

        if not duree:
            return self.TIMEOUT_MIN

        return int(min(
            self.TIMEOUT_MAX,
            max(self.TIMEOUT_MIN, duree / 60.0 * self.TIMEOUT_PAR_MINUTE_AUDIO)
        ))

    def transcribe_file(self, file_path, language=None):
        """
        Transcrit un fichier audio en texte

        Args:
            file_path: Chemin vers le fichier audio
            language: Code de langue. None (défaut) => DEFAULT_LANGUAGE
                ('multi'), qui couvre l'intégralité de l'audio même bruité.
                Ne passer une langue explicite ('fr', 'en'...) que pour un
                besoin précis : une langue mono-langue fait perdre les
                passages où plusieurs voix se superposent.

        Returns:
            dict: {
                'success': bool,
                'transcript': str,
                'confidence': float,
                'words': list,
                'duration': float,   # durée réelle du fichier (secondes)
                'covered_until': float,  # fin du dernier mot transcrit
                'coverage': float,   # % de l'audio réellement transcrit
                'error': str (si erreur)
            }
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Service Deepgram non configuré (clé API manquante)'
            }
        
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f'Fichier non trouvé: {file_path}'
            }
        
        try:
            logger.info(f"🎤 Transcription Deepgram: {file_path}")

            # Déterminer le type MIME
            mime_type = self._get_mime_type(file_path)

            # Lire le fichier audio
            with open(file_path, 'rb') as audio_file:
                audio_data = audio_file.read()

            # Timeout adaptatif dimensionné sur la durée de l'audio
            file_size_mb = len(audio_data) / (1024 * 1024)
            adaptive_timeout = self._adaptive_timeout(file_path, len(audio_data))
            logger.info(
                f"📡 Deepgram: envoi de {file_size_mb:.1f}MB, "
                f"timeout adaptatif: {adaptive_timeout}s ({adaptive_timeout//60}min)"
            )

            # Appel à l'API Deepgram
            statut, result, corps = self._envoyer(
                audio_data, mime_type, adaptive_timeout, language
            )

            if statut == 200 and result is not None:
                # Extraire la transcription
                confidence = self._extract_confidence(result)
                words = self._extract_words(result)
                duration = self._extract_duration(result)

                # Passages sans aucun mot : on les re-transcrit isolément
                # (tâche 36). Sans cela, un trou au milieu du cours — ou une
                # queue entière perdue — restait invisible et produisait un
                # résumé incomplet.
                words, recuperation = self._recuperer_passages_manquants(
                    file_path, words, duration
                )
                # Le texte n'est reconstruit QUE si des mots ont été
                # récupérés : sans trou, la sortie de Deepgram est conservée
                # telle quelle (mise en forme `smart_format` / paragraphes).
                transcript = (
                    self._texte_depuis_mots(words) if recuperation
                    else self._extract_transcript(result)
                )
                covered_until, coverage = self._couverture_mots(words, duration)

                logger.info(
                    f"✅ Transcription réussie: {len(transcript)} caractères, "
                    f"{len(words)} mots, couverture {coverage:.1f}% "
                    f"({covered_until:.1f}s / {duration:.1f}s)"
                )

                # Un audio à peine couvert signifie que des passages entiers
                # ont été perdus : le résumé qui en découle sera tronqué.
                # On le rend visible ici — c'est précisément ce silence qui
                # masquait le problème (statut 'completed' + confiance élevée
                # alors que la moitié du cours manquait).
                if coverage and coverage < self.SEUIL_COUVERTURE:
                    logger.warning(
                        f"⚠️ TRANSCRIPTION INCOMPLÈTE pour {file_path} : "
                        f"seuls {coverage:.1f}% de l'audio sont transcrits "
                        f"(dernier mot à {covered_until:.1f}s sur "
                        f"{duration:.1f}s, soit {duration - covered_until:.0f}s "
                        f"manquantes). Le résumé généré sera incomplet."
                    )

                return {
                    'success': True,
                    'transcript': transcript,
                    'confidence': confidence,
                    'words': words,
                    'duration': duration,
                    'covered_until': covered_until,
                    'coverage': coverage,
                    'raw_response': result
                }
            else:
                error_msg = f"Erreur API Deepgram: {statut} - {corps}"
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024) if os.path.exists(file_path) else 0
            return {
                'success': False,
                'error': f'Timeout Deepgram après {adaptive_timeout}s pour fichier de {file_size_mb:.1f}MB. Le fichier est peut-être trop volumineux.'
            }
        except Exception as e:
            logger.error(f"❌ Erreur transcription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def transcribe_bytes(self, audio_bytes, mime_type='audio/wav', language=None):
        """
        Transcrit des bytes audio en texte

        Args:
            audio_bytes: Données audio en bytes
            mime_type: Type MIME de l'audio
            language: Code de langue (None => DEFAULT_LANGUAGE)

        Returns:
            dict: Résultat de la transcription
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Service Deepgram non configuré'
            }

        try:
            logger.info(f"🎤 Transcription Deepgram (bytes): {len(audio_bytes)} bytes")

            params = {
                'model': self.MODEL,
                'language': language or self.DEFAULT_LANGUAGE,
                'punctuate': 'true',
                'paragraphs': 'true',
                'smart_format': 'true',
            }
            
            headers = {
                'Authorization': f'Token {self.api_key}',
                'Content-Type': mime_type,
            }
            
            # Timeout adaptatif dimensionné sur la durée de l'audio
            bytes_size_mb = len(audio_bytes) / (1024 * 1024)
            adaptive_timeout = self._adaptive_timeout(size_bytes=len(audio_bytes))
            logger.info(f"📡 Deepgram bytes: {bytes_size_mb:.1f}MB, timeout: {adaptive_timeout}s")
            
            response = requests.post(
                self.base_url,
                params=params,
                headers=headers,
                data=audio_bytes,
                timeout=adaptive_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                transcript = self._extract_transcript(result)
                confidence = self._extract_confidence(result)
                duration = self._extract_duration(result)
                covered_until, coverage = self._compute_coverage(result, duration)

                if coverage and coverage < self.SEUIL_COUVERTURE:
                    logger.warning(
                        f"⚠️ TRANSCRIPTION INCOMPLÈTE (bytes) : "
                        f"{coverage:.1f}% de l'audio transcrit "
                        f"({covered_until:.1f}s / {duration:.1f}s)"
                    )

                return {
                    'success': True,
                    'transcript': transcript,
                    'confidence': confidence,
                    'duration': duration,
                    'covered_until': covered_until,
                    'coverage': coverage,
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur API: {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ── Récupération des passages manquants (tâche 36) ──────────────────────

    def _envoyer(self, donnees, mime_type, timeout, language=None):
        """
        Envoie un bloc audio à Deepgram.

        Returns:
            tuple: (statut HTTP, json ou None, corps de la réponse)

        Point unique d'envoi : le fichier entier et les segments de
        récupération utilisent ainsi EXACTEMENT les mêmes paramètres — un
        segment transcrit avec d'autres options ne serait pas comparable.
        """
        reponse = requests.post(
            self.base_url,
            params={
                'model': self.MODEL,
                'language': language or self.DEFAULT_LANGUAGE,
                'punctuate': 'true',
                'paragraphs': 'true',
                'smart_format': 'true',
                'diarize': 'false',  # Pas de détection de locuteurs (non
                                     # consommée en aval ; sans effet mesuré
                                     # sur la couverture de l'audio)
            },
            headers={
                'Authorization': f'Token {self.api_key}',
                'Content-Type': mime_type,
            },
            data=donnees,
            timeout=timeout,
        )
        charge = None
        if reponse.status_code == 200:
            try:
                charge = reponse.json()
            except ValueError:
                logger.warning("⚠️ Réponse Deepgram 200 illisible (JSON invalide)")
        return reponse.status_code, charge, reponse.text

    def _trouver_trous(self, words, duration):
        """
        Liste les passages de l'audio qu'AUCUN mot ne recouvre.

        Deux sortes de trous, traitées de la même façon :
          - internes : entre la fin d'un mot et le début du suivant ;
          - final : entre la fin du dernier mot et la fin du fichier (c'est le
            symptôme historique : la transcription s'arrête à mi-parcours).

        Returns:
            list[tuple]: [(début, fin), …] en secondes
        """
        trous = []
        for precedent, suivant in zip(words, words[1:]):
            fin = float(precedent.get('end') or 0.0)
            debut = float(suivant.get('start') or 0.0)
            if debut - fin >= self.SEUIL_TROU:
                trous.append((fin, debut))

        if duration:
            fin = float(words[-1].get('end') or 0.0) if words else 0.0
            if duration - fin >= self.SEUIL_TROU:
                trous.append((fin, duration))
        return trous

    def _extraire_segment(self, file_path, debut_s, fin_s, dossier):
        """
        Écrit un fichier autonome ne contenant que [debut_s, fin_s[.

        Écriture SANS ré-encodage : un AMR est une suite de trames de 20 ms,
        il suffit de recopier celles de la fenêtre. Un ré-encodage (ffmpeg)
        dégraderait l'audio et pourrait recréer le problème qu'on corrige.

        Returns:
            str|None: chemin du segment, ou None si le format n'est pas
            découpable sans ré-encodage.
        """
        if not self._est_amr(file_path):
            logger.info(
                f"ℹ️ Format non AMR ({os.path.splitext(file_path)[1]}) : "
                f"pas de récupération par découpage pour ce fichier"
            )
            return None

        with open(file_path, 'rb') as f:
            donnees = f.read()

        entete = donnees[:6]
        i = 6
        numero = 0
        trames = []
        while i < len(donnees):
            mode = (donnees[i] >> 3) & 0x0F
            taille = self.TAILLE_TRAME_AMR[mode]
            if taille == 0 or i + taille > len(donnees):
                break  # trame illisible : on s'arrête là, comme un décodeur
            t = numero * self.DUREE_TRAME_AMR
            if debut_s <= t < fin_s:
                trames.append(donnees[i:i + taille])
            numero += 1
            i += taille

        if not trames:
            return None

        chemin = os.path.join(dossier, f'seg_{int(debut_s)}_{int(fin_s)}.amr')
        with open(chemin, 'wb') as f:
            f.write(entete)
            f.writelines(trames)
        return chemin

    def _est_amr(self, file_path):
        """Vrai si le fichier est un AMR (bande étroite ou large)."""
        try:
            with open(file_path, 'rb') as f:
                return f.read(9).startswith((b'#!AMR\n', b'#!AMR-WB\n'))
        except OSError:
            return False

    def _recuperer_passages_manquants(self, file_path, words, duration):
        """
        Re-transcrit isolément les passages qu'aucun mot ne recouvre, puis les
        recolle à leur position réelle.

        Ne peut qu'AJOUTER des mots : les mots déjà transcrits sont conservés
        tels quels. Le coût est borné (DUREE_MAX_RECUPERATION, MAX_SEGMENTS) et
        nul pour un audio sans trou — le cas courant reste un seul appel.

        Returns:
            tuple: (mots fusionnés, vrai si au moins un passage a été récupéré)
        """
        if not duration or not words:
            return words, False

        trous = self._trouver_trous(words, duration)
        if not trous:
            return words, False

        logger.info(
            f"🔎 {len(trous)} passage(s) sans aucun mot détecté(s) : "
            + ', '.join(f'{d:.1f}s→{f:.1f}s' for d, f in trous)
        )

        recuperes = []
        duree_recuperee = 0.0

        with tempfile.TemporaryDirectory() as dossier:
            for debut, fin in trous[:self.MAX_SEGMENTS]:
                if duree_recuperee >= self.DUREE_MAX_RECUPERATION:
                    logger.info("ℹ️ Plafond de récupération atteint, trous restants ignorés")
                    break
                if fin - debut > self.DUREE_MAX_RECUPERATION - duree_recuperee:
                    fin = debut + (self.DUREE_MAX_RECUPERATION - duree_recuperee)

                try:
                    chemin = self._extraire_segment(file_path, debut, fin, dossier)
                    if not chemin:
                        continue

                    with open(chemin, 'rb') as f:
                        donnees = f.read()

                    # Un segment ne dépasse jamais DUREE_MAX_RECUPERATION
                    # d'audio : le plancher de timeout suffit largement.
                    statut, resultat, corps = self._envoyer(
                        donnees, 'audio/amr', self.TIMEOUT_MIN
                    )
                    if statut != 200 or resultat is None:
                        logger.warning(
                            f"⚠️ Segment {debut:.1f}s→{fin:.1f}s : Deepgram a "
                            f"répondu {statut} — passage non récupéré"
                        )
                        continue

                    mots_segment = self._extract_words(resultat)
                    if not mots_segment:
                        logger.info(
                            f"ℹ️ Segment {debut:.1f}s→{fin:.1f}s : aucun mot — "
                            f"passage réellement inexploitable (parole masquée)"
                        )
                        continue

                    # Les temps du segment sont relatifs à son début : on les
                    # ramène sur la timeline du fichier complet.
                    for mot in mots_segment:
                        for cle in ('start', 'end'):
                            if mot.get(cle) is not None:
                                mot[cle] = float(mot[cle]) + debut
                    recuperes.extend(mots_segment)
                    duree_recuperee += (fin - debut)
                    logger.info(
                        f"✅ Segment {debut:.1f}s→{fin:.1f}s récupéré : "
                        f"{len(mots_segment)} mots"
                    )
                except Exception as e:
                    logger.warning(
                        f"⚠️ Récupération du passage {debut:.1f}s→{fin:.1f}s "
                        f"impossible : {type(e).__name__}: {e}"
                    )

        # ⚠️ Ces bilans sont volontairement au niveau WARNING : le logger
        # `courses` n'est pas déclaré dans LOGGING, donc seuls les WARNING
        # remontent réellement en production (le logger racine n'a aucun
        # handler). Au niveau INFO, tout ce diagnostic resterait invisible —
        # c'est exactement ce qui a masqué le problème jusqu'ici.
        if not recuperes:
            logger.warning(
                f"⚠️ {len(trous)} passage(s) sans aucun mot sur "
                f"{os.path.basename(file_path)} — aucun mot récupérable "
                f"(parole masquée par le bruit) : "
                + ', '.join(f'{d:.0f}s→{f:.0f}s' for d, f in trous)
            )
            return words, False

        fusionnes = sorted(
            list(words) + recuperes, key=lambda m: float(m.get('start') or 0.0)
        )
        restants = self._trouver_trous(fusionnes, duration)
        logger.warning(
            f"⚠️ {len(trous)} passage(s) sans mot détecté(s) sur "
            f"{os.path.basename(file_path)} : {len(recuperes)} mots récupérés "
            f"par découpage ({duree_recuperee:.0f}s ré-audio), "
            f"{len(restants)} passage(s) restent inexploitables "
            f"({sum(f - d for d, f in restants):.0f}s d'audio)"
        )
        return fusionnes, True

    @staticmethod
    def _texte_depuis_mots(words):
        """
        Reconstruit le texte à partir des mots horodatés.

        `punctuated_word` porte la ponctuation et la casse produites par
        `smart_format` — on préfère donc ce champ à `word`.
        """
        morceaux = []
        for mot in words:
            texte = mot.get('punctuated_word') or mot.get('word') or ''
            if texte.strip():
                morceaux.append(texte.strip())
        return ' '.join(morceaux)

    @staticmethod
    def _couverture_mots(words, duration):
        """Fin du dernier mot et pourcentage de l'audio couvert, en secondes."""
        try:
            fin = float(words[-1].get('end') or 0.0) if words else 0.0
            if not duration:
                return fin, 0.0
            return fin, max(0.0, min(100.0, fin / duration * 100))
        except Exception as e:
            logger.warning(f"⚠️ Impossible de calculer la couverture audio: {e}")
            return 0.0, 0.0

    def _get_mime_type(self, file_path):
        """Détermine le type MIME basé sur l'extension"""
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.mp4': 'audio/mp4',
            '.ogg': 'audio/ogg',
            '.oga': 'audio/ogg',
            '.opus': 'audio/opus',
            '.webm': 'audio/webm',
            '.flac': 'audio/flac',
            # Formats utilisés par les enregistreurs mobiles (dictaphones,
            # applications d'enregistrement de cours). Sans ces entrées, on
            # envoyait 'audio/wav' pour un fichier AMR/3GP, ce qui dégradait
            # la transcription (mots perdus, mesuré lors du diagnostic).
            '.amr': 'audio/amr',
            '.3gp': 'audio/3gpp',
            '.3gpp': 'audio/3gpp',
            '.aac': 'audio/aac',
            '.aiff': 'audio/aiff',
            '.aif': 'audio/aiff',
            '.wma': 'audio/x-ms-wma',
            '.caf': 'audio/x-caf',
            '.m4b': 'audio/mp4',
            '.mpga': 'audio/mpeg',
            '.amr-wb': 'audio/amr-wb',
            '.awb': 'audio/amr-wb',
            '.gsm': 'audio/gsm',
        }
        if ext in mime_types:
            return mime_types[ext]

        # Repli sur la bibliothèque standard avant le défaut audio/wav :
        # elle connaît davantage de formats que la table ci-dessus.
        devine, _ = mimetypes.guess_type(file_path)
        if devine and devine.startswith('audio/'):
            logger.warning(
                f"⚠️ Extension {ext} absente de la table MIME, "
                f"type déduit par mimetypes : {devine}"
            )
            return devine

        logger.warning(
            f"⚠️ Extension audio inconnue {ext} pour {file_path}, "
            f"repli sur audio/wav (la transcription peut être dégradée)"
        )
        return 'audio/wav'
    
    def _extract_transcript(self, result):
        """Extrait le texte transcrit du résultat Deepgram"""
        try:
            channels = result.get('results', {}).get('channels', [])
            if channels:
                alternatives = channels[0].get('alternatives', [])
                if alternatives:
                    return alternatives[0].get('transcript', '')
        except Exception as e:
            logger.error(f"Erreur extraction transcript: {e}")
        return ''
    
    def _extract_confidence(self, result):
        """Extrait le score de confiance"""
        try:
            channels = result.get('results', {}).get('channels', [])
            if channels:
                alternatives = channels[0].get('alternatives', [])
                if alternatives:
                    return alternatives[0].get('confidence', 0.0)
        except Exception:
            pass
        return 0.0
    
    def _extract_words(self, result):
        """Extrait les mots avec leurs timestamps"""
        try:
            channels = result.get('results', {}).get('channels', [])
            if channels:
                alternatives = channels[0].get('alternatives', [])
                if alternatives:
                    return alternatives[0].get('words', [])
        except Exception:
            pass
        return []

    def _extract_duration(self, result):
        """
        Extrait la durée réelle de l'audio, telle que mesurée par Deepgram.

        C'est la seule durée fiable côté backend : ffprobe n'est pas installé
        en production et le repli sur la taille du fichier est très grossier.
        """
        try:
            duree = (result.get('metadata') or {}).get('duration')
            return float(duree) if duree else 0.0
        except (TypeError, ValueError):
            logger.warning("⚠️ Durée audio illisible dans la réponse Deepgram")
            return 0.0

    def _compute_coverage(self, result, duration):
        """
        Mesure la part de l'audio réellement transcrite.

        Compare la fin du dernier mot finalisé à la durée totale du fichier.
        Un écart important = des passages entiers ont été perdus, quelle que
        soit la confiance annoncée par Deepgram.

        ⚠️ Ce taux ne voit que la FIN du dernier mot : un trou AU MILIEU du
        fichier ne l'affecte pas. Les trous internes sont mesurés séparément
        par `_trouver_trous` (tâche 36).

        Returns:
            tuple: (fin_du_dernier_mot, pourcentage_couvert)
        """
        return self._couverture_mots(self._extract_words(result), duration)


# Instance globale du service
deepgram_service = DeepgramService()
