"""
TEST TACHE 36 — la transcription va-t-elle jusqu'au bout de l'audio ?

Teste le service RÉELLEMENT utilisé en production
(`courses.deepgram_service.deepgram_service`), pas une copie.

Deux cas :

  1. Configuration actuelle (nova-3 + multi) sur l'audio clair et l'audio
     bruité : combien de passages restent sans aucun mot après récupération ?

  2. ANCIENNE configuration (nova-2 + fr — celle qui est aujourd'hui déployée
     et qui tronque la transcription) : on compare l'appel brut, qui s'arrête
     à mi-fichier, et le même appel suivi de la récupération des passages
     perdus. C'est la preuve que la correction protège même si la
     configuration redevient défavorable.

Ce script n'écrit RIEN en base et ne modifie aucun fichier du projet.
"""

import os
import sys

import django

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from courses.deepgram_service import DeepgramService, deepgram_service  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEP = '=' * 78


def titre(txt):
    print(f'\n{SEP}\n{txt}\n{SEP}')


def appel_brut(file_path):
    """Un seul appel sur le fichier entier, SANS récupération des trous."""
    with open(file_path, 'rb') as f:
        donnees = f.read()
    statut, resultat, corps = deepgram_service._envoyer(
        donnees,
        deepgram_service._get_mime_type(file_path),
        deepgram_service._adaptive_timeout(file_path, len(donnees)),
    )
    if statut != 200 or resultat is None:
        return None
    mots = deepgram_service._extract_words(resultat)
    duree = deepgram_service._extract_duration(resultat)
    return {
        'mots': mots,
        'duree': duree,
        'couverture': deepgram_service._couverture_mots(mots, duree)[1],
        'trous': deepgram_service._trouver_trous(mots, duree),
    }


def afficher(libelle, etat):
    if etat is None:
        print(f'   {libelle} : échec de l\'appel')
        return
    print(f'   {libelle}')
    print(f'      mots           : {len(etat["mots"])}')
    print(f'      couverture     : {etat["couverture"]:.1f} %')
    if etat['trous']:
        for debut, fin in etat['trous']:
            print(f'      trou restant   : {debut:.1f}s → {fin:.1f}s '
                  f'({fin - debut:.1f}s)')
    else:
        print('      aucun passage sans mot')


def etat_service(file_path):
    """Passe par le chemin de production complet (récupération comprise)."""
    resultat = deepgram_service.transcribe_file(file_path)
    if not resultat.get('success'):
        return None
    return {
        'mots': resultat['words'],
        'duree': resultat['duration'],
        'couverture': resultat['coverage'],
        'trous': deepgram_service._trouver_trous(
            resultat['words'], resultat['duration']
        ),
    }


def main():
    clair = os.path.join(RACINE, 'audio_test_claire.amr')
    bruite = os.path.join(RACINE, 'audio_test.amr')

    titre('CAS 1 — configuration actuelle (nova-3 + multi) + récupération')
    for etiquette, chemin in (('clair ', clair), ('bruité', bruite)):
        if not os.path.exists(chemin):
            print(f'   {etiquette} : fichier absent')
            continue
        print(f'\n  AUDIO {etiquette}')
        afficher('après récupération (chemin de production)', etat_service(chemin))

    titre("CAS 2 — ancienne configuration déployée (nova-2 + fr)")
    print("  Cette configuration tronque la transcription. On vérifie que la")
    print("  récupération des passages perdus la rend inoffensive.\n")

    modele, langue = DeepgramService.MODEL, DeepgramService.DEFAULT_LANGUAGE
    DeepgramService.MODEL = 'nova-2'
    DeepgramService.DEFAULT_LANGUAGE = 'fr'
    try:
        brut = appel_brut(bruite)
        afficher('audio bruité — appel brut (ce que fait la production aujourd\'hui)', brut)

        apres = etat_service(bruite)
        afficher("audio bruité — même configuration + récupération", apres)

        if brut and apres:
            print(f'\n   ➜ mots récupérés : {len(apres["mots"]) - len(brut["mots"])}')
            print(f'   ➜ couverture     : {brut["couverture"]:.1f} % '
                  f'→ {apres["couverture"]:.1f} %')
    finally:
        DeepgramService.MODEL, DeepgramService.DEFAULT_LANGUAGE = modele, langue

    print(f'\n{SEP}\n')


if __name__ == '__main__':
    sys.exit(main())
