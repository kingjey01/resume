"""
TEST TACHE 33 -- Verification que la transcription couvre TOUT l'audio.

Trois cas, testes via le service reellement utilise en production
(courses.deepgram_service.deepgram_service) :

    1. audio clair        : audio_test_claire.amr
    2. audio bruite       : audio_test.amr (voix parasites en fond)
    3. audio long         : ~3 h, pour verifier le timeout et la couverture

Le 3e cas est construit SANS ffmpeg : un fichier AMR est un en-tete de
6 octets ("#!AMR\\n") suivi de trames brutes, donc concatener les trames
produit un AMR valide dont la duree s'additionne. Le fichier temporaire est
supprime a la fin du test.

Ce script n'ecrit RIEN en base et ne modifie aucun fichier du projet.
"""

import os
import sys
import time

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from courses.deepgram_service import deepgram_service  # noqa: E402
from courses.audio_processing import audio_processor  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEP = '=' * 78
ENTETE_AMR = b'#!AMR\n'


def titre(txt):
    print(f"\n{SEP}\n{txt}\n{SEP}")


def construire_audio_long(source, nb_copies, destination):
    """Concatene les trames AMR pour obtenir un audio de duree cumulee."""
    with open(source, 'rb') as f:
        contenu = f.read()

    if not contenu.startswith(ENTETE_AMR):
        print("  [INFO] En-tete AMR inattendu, abandon de la concatenation")
        return None

    entete, trames = contenu[:len(ENTETE_AMR)], contenu[len(ENTETE_AMR):]
    with open(destination, 'wb') as f:
        f.write(entete)
        for _ in range(nb_copies):
            f.write(trames)

    print(f"  {nb_copies} copies de {os.path.basename(source)} -> "
          f"{os.path.getsize(destination) / 1024 / 1024:.1f} MB")
    return destination


def tester(label, chemin, attendu_fin=None):
    """Transcrit un audio via le service de production et mesure la couverture."""
    print(f"\n--- {label} : {os.path.basename(chemin)} "
          f"({os.path.getsize(chemin) / 1024 / 1024:.2f} MB)")

    timeout_annonce = deepgram_service._adaptive_timeout(chemin, os.path.getsize(chemin))
    print(f"  Timeout retenu : {timeout_annonce}s ({timeout_annonce // 60} min)")

    t0 = time.time()
    res = deepgram_service.transcribe_file(chemin)   # <- code de production
    ecoule = time.time() - t0

    if not res.get('success'):
        print(f"  [ECHEC] {res.get('error')}")
        return None

    duree = res['duration']
    couv = res['coverage']
    fin = res['covered_until']
    texte = res['transcript']

    print(f"  Duree appel reel : {ecoule:.1f}s")
    print(f"  Duree audio      : {duree:.1f}s ({duree/60:.1f} min)")
    print(f"  Mots transcrits  : {len(res['words'])}")
    print(f"  Longueur texte   : {len(texte)} caracteres")
    print(f"  Transcrit jusqu'a: {fin:.1f}s")
    print(f"  COUVERTURE       : {couv:.1f}%")

    if couv >= deepgram_service.SEUIL_COUVERTURE:
        print(f"  => OK : l'audio est couvert jusqu'a sa fin reelle")
    else:
        print(f"  => INCOMPLET : {duree - fin:.0f}s d'audio non transcrites")

    if attendu_fin:
        ok = attendu_fin.lower() in texte.lower()
        print(f"  Phrase finale attendue {'TROUVEE' if ok else 'ABSENTE'} : "
              f"{attendu_fin!r}")
    print(f"  Fin du texte : ...{texte[-110:]!r}")

    return {'couv': couv, 'duree': duree, 'fin': fin,
            'mots': len(res['words']), 'car': len(texte), 'ecoule': ecoule}


def main():
    print(SEP)
    print("TEST TACHE 33 -- COUVERTURE COMPLETE DE LA TRANSCRIPTION")
    print(SEP)
    print(f"Modele : {deepgram_service.MODEL} | Langue : "
          f"{deepgram_service.DEFAULT_LANGUAGE} | Seuil : "
          f"{deepgram_service.SEUIL_COUVERTURE}%")

    if not deepgram_service.is_configured():
        print("[ERREUR] DEEPGRAM_API_KEY non configuree")
        return

    resultats = {}
    clair = os.path.join(RACINE, 'audio_test_claire.amr')
    bruite = os.path.join(RACINE, 'audio_test.amr')

    # La video se termine par cette phrase : si elle apparait, la
    # transcription a bien atteint la fin reelle du cours.
    PHRASE_FINALE = "séquence est terminée"

    # 1 et 2 : les deux audios de comparaison fournis
    resultats['clair'] = tester('CAS 1 - audio clair', clair, PHRASE_FINALE)
    resultats['bruite'] = tester('CAS 2 - audio bruite (voix parasites)',
                                 bruite, PHRASE_FINALE)

    # 3 : audio long (~3 h), construit par concatenation des trames AMR
    titre("CAS 3 - AUDIO LONG (~3 h)")
    temporaire = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              '_diag_tache33_audio_long.amr')
    try:
        if construire_audio_long(bruite, 27, temporaire):
            resultats['long'] = tester('CAS 3 - audio long', temporaire, PHRASE_FINALE)
    finally:
        if os.path.exists(temporaire):
            os.remove(temporaire)
            print(f"\n  (fichier temporaire supprime : {temporaire})")

    titre("SYNTHESE DU TEST")
    print(f"{'cas':10s} {'duree audio':>12s} {'couverture':>11s} {'mots':>7s} "
          f"{'car':>7s} {'appel':>7s}")
    for k, r in resultats.items():
        if not r:
            print(f"{k:10s} ECHEC")
            continue
        print(f"{k:10s} {r['duree']:11.1f}s {r['couv']:10.1f}% {r['mots']:7d} "
              f"{r['car']:7d} {r['ecoule']:6.1f}s")

    ok = all(r and r['couv'] >= deepgram_service.SEUIL_COUVERTURE
             for r in resultats.values())
    print(f"\nRESULTAT GLOBAL : {'TOUS LES CAS COUVERTS' if ok else 'AU MOINS UN CAS INCOMPLET'}")


if __name__ == '__main__':
    main()
