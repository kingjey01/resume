"""
Tests (sans réseau) des mécanismes de récupération des passages perdus.

Ces tests couvrent la logique pure de la tâche 36 : détection des passages
qu'aucun mot ne recouvre, découpage sans perte d'un AMR, reconstruction du
texte et calcul de couverture. Le test de bout en bout contre la vraie API est
dans `backend/test_tache36_recuperation.py` (script, hors suite Django).
"""

import os
import tempfile

from django.test import TestCase

from .deepgram_service import DeepgramService, deepgram_service

ENTETE_AMR = b'#!AMR\n'


def _fichier_amr(chemin, nb_trames, octet_trame=b'\x3c'):
    """
    Écrit un AMR-NB valide de `nb_trames` trames de 20 ms.

    Une trame de mode 7 (12,2 kbit/s) occupe 32 octets en-tête compris :
    l'octet d'en-tête 0x3c (mode 7, qualité 1) suivi de 31 octets de données.
    """
    with open(chemin, 'wb') as f:
        f.write(ENTETE_AMR)
        for i in range(nb_trames):
            f.write(octet_trame + bytes([i % 251] * 31))


def _mot(debut, fin):
    return {'start': debut, 'end': fin, 'word': 'x', 'punctuated_word': 'X.'}


class TrouverTrousTest(TestCase):
    """Détection des passages de l'audio qu'aucun mot ne recouvre."""

    def test_aucun_trou_sur_une_transcription_complete(self):
        mots = [_mot(0, 10), _mot(12, 20), _mot(21, 30)]

        self.assertEqual(deepgram_service._trouver_trous(mots, 30.5), [])

    def test_trou_interne_detecte(self):
        mots = [_mot(0, 10), _mot(45, 60)]

        trous = deepgram_service._trouver_trous(mots, 60)

        self.assertEqual(trous, [(10.0, 45.0)])

    def test_queue_perdue_detectee(self):
        """Le symptôme de production : la transcription s'arrête à mi-fichier."""
        # 5 s entre les deux mots : une simple respiration, pas un trou.
        mots = [_mot(0, 100), _mot(105, 220)]

        trous = deepgram_service._trouver_trous(mots, 391.2)

        self.assertEqual(trous, [(220.0, 391.2)])

    def test_respiration_courte_ignoree(self):
        """Une pause de quelques secondes n'est pas un passage perdu."""
        mots = [_mot(0, 10), _mot(15, 30)]

        self.assertEqual(deepgram_service._trouver_trous(mots, 30), [])

    def test_plusieurs_trous_dans_l_ordre(self):
        mots = [_mot(0, 10), _mot(40, 60), _mot(120, 150)]

        trous = deepgram_service._trouver_trous(mots, 200)

        self.assertEqual(trous, [(10.0, 40.0), (60.0, 120.0), (150.0, 200.0)])


class ExtraireSegmentTest(TestCase):
    """Découpage d'un AMR : recopie de trames, sans ré-encodage."""

    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.source = os.path.join(self.dossier, 'source.amr')

    def test_aucun_mot_donc_aucune_recuperation(self):
        """Une transcription vide ne déclenche pas de ré-essai coûteux."""
        mots, recupere = deepgram_service._recuperer_passages_manquants(
            self.source, [], 391.2
        )

        self.assertEqual(mots, [])
        self.assertFalse(recupere)

    def test_transcription_complete_ne_declenche_rien(self):
        """Cas courant : un seul appel, aucune récupération (coût inchangé)."""
        mots = [_mot(0, 100), _mot(105, 400)]
        _, recupere = deepgram_service._recuperer_passages_manquants(
            self.source, mots, 403.2
        )

        self.assertFalse(recupere)

    def test_segment_contient_exactement_la_fenetre_demandee(self):
        _fichier_amr(self.source, nb_trames=10)  # 10 trames = 0,2 s

        chemin = deepgram_service._extraire_segment(self.source, 0.04, 0.12, self.dossier)

        self.assertIsNotNone(chemin)
        with open(chemin, 'rb') as f:
            segment = f.read()
        with open(self.source, 'rb') as f:
            source = f.read()

        self.assertTrue(segment.startswith(ENTETE_AMR))
        # Trames 2 à 5 (t = 0,04 / 0,06 / 0,08 / 0,10), soit 4 × 32 octets.
        self.assertEqual(len(segment), len(ENTETE_AMR) + 4 * 32)
        # Recopie à l'identique des trames de la fenêtre.
        self.assertEqual(
            segment[len(ENTETE_AMR):],
            source[len(ENTETE_AMR) + 2 * 32: len(ENTETE_AMR) + 6 * 32],
        )

    def test_segment_jusqu_a_la_fin_du_fichier(self):
        _fichier_amr(self.source, nb_trames=10)

        chemin = deepgram_service._extraire_segment(self.source, 0.16, 0.20, self.dossier)

        with open(chemin, 'rb') as f:
            segment = f.read()
        self.assertEqual(len(segment), len(ENTETE_AMR) + 2 * 32)

    def test_fichier_non_amr_non_decoupable(self):
        """Aucun ré-encodage n'est tenté : mieux vaut ne rien faire que dégrader."""
        autre = os.path.join(self.dossier, 'audio.m4a')
        with open(autre, 'wb') as f:
            f.write(b'\x00\x00\x00\x20ftypM4A ')

        self.assertIsNone(
            deepgram_service._extraire_segment(autre, 1.0, 2.0, self.dossier)
        )

    def test_fenetre_sans_trame_retourne_none(self):
        _fichier_amr(self.source, nb_trames=3)  # 0,06 s

        self.assertIsNone(
            deepgram_service._extraire_segment(self.source, 5.0, 6.0, self.dossier)
        )


class TexteDepuisMotsTest(TestCase):
    """Reconstruction du texte après recollage des passages récupérés."""

    def test_ponctuation_conservee(self):
        mots = [
            {'punctuated_word': 'Bonjour,'},
            {'punctuated_word': 'les'},
            {'punctuated_word': 'étudiants.'},
        ]

        self.assertEqual(
            deepgram_service._texte_depuis_mots(mots), 'Bonjour, les étudiants.'
        )

    def test_repli_sur_le_mot_brut(self):
        mots = [{'word': 'sans'}, {'word': 'ponctuation'}]

        self.assertEqual(
            deepgram_service._texte_depuis_mots(mots), 'sans ponctuation'
        )

    def test_mots_vides_ignores(self):
        mots = [{'punctuated_word': 'a'}, {'punctuated_word': '  '}, {'punctuated_word': 'b'}]

        self.assertEqual(deepgram_service._texte_depuis_mots(mots), 'a b')


class CouvertureMotsTest(TestCase):
    def test_couverture_normale(self):
        fin, pct = deepgram_service._couverture_mots([_mot(0, 100), _mot(110, 200)], 400)

        self.assertEqual(fin, 200.0)
        self.assertEqual(pct, 50.0)

    def test_sans_duree_connue(self):
        fin, pct = deepgram_service._couverture_mots([_mot(0, 100)], 0)

        self.assertEqual(fin, 100.0)
        self.assertEqual(pct, 0.0)

    def test_sans_mot(self):
        fin, pct = deepgram_service._couverture_mots([], 400)

        self.assertEqual((fin, pct), (0.0, 0.0))

    def test_couverture_plafonnee_a_100(self):
        _, pct = deepgram_service._couverture_mots([_mot(0, 410)], 400)

        self.assertEqual(pct, 100.0)


class ConfigurationTest(TestCase):
    """La configuration retenue est bien celle qui couvre tout l'audio."""

    def test_modele_et_langue(self):
        self.assertEqual(DeepgramService.MODEL, 'nova-3')
        self.assertEqual(DeepgramService.DEFAULT_LANGUAGE, 'multi')

    def test_bornes_de_recuperation(self):
        self.assertGreater(DeepgramService.SEUIL_TROU, 0)
        self.assertGreater(DeepgramService.DUREE_MAX_RECUPERATION, DeepgramService.SEUIL_TROU)
        self.assertGreater(DeepgramService.MAX_SEGMENTS, 0)

    def test_table_des_tailles_de_trame_amr(self):
        # Modes 0 à 7 : 13 à 32 octets, en-tête compris.
        self.assertEqual(DeepgramService.TAILLE_TRAME_AMR[:8], (13, 14, 16, 18, 20, 21, 27, 32))
        # Mode 8 : SID (silence) ; mode 15 : No Data (en-tête seul).
        self.assertEqual(DeepgramService.TAILLE_TRAME_AMR[8], 6)
        self.assertEqual(DeepgramService.TAILLE_TRAME_AMR[15], 1)
