"""
Diagnostic tâche 36 — un passage perdu peut-il être récupéré en le découpant ?

Constat de départ (diagnostic_tache36_couverture.py) : sur l'audio bruité, même
avec la configuration actuelle (nova-3 + multi), trois passages ne produisent
AUCUN mot — dont un de 35 s après 40,6 s — alors que le taux de couverture
global affiche 99,9 % (il ne mesure que la fin du dernier mot).

Ce script teste l'hypothèse : ces passages sont-ils réellement inaudibles, ou
l'appel sur le fichier ENTIER les perd-il ? On extrait le passage concerné dans
un fichier AMR autonome (le découpage AMR est sans perte : il suffit de copier
les trames) et on le transcrit seul.

Un fichier AMR-NB est une suite de trames de 20 ms ; la taille totale d'une
trame (en-tête de 1 octet compris) dépend de son mode :
    mode 0..7  -> 13, 14, 16, 18, 20, 21, 27, 32 octets
    mode 8     -> 6 octets (SID, silence)
    mode 15    -> 1 octet  (No Data)

Usage (depuis backend/) :
    .venv/Scripts/python.exe diagnostic_tache36_segments.py
"""

import os
import sys

import django
import requests

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from courses.deepgram_service import deepgram_service  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TAILLE_TRAME = [13, 14, 16, 18, 20, 21, 27, 32, 6, 0, 0, 0, 0, 0, 0, 1]
DUREE_TRAME = 0.02  # 20 ms


def decouper(file_path, debut_s, fin_s, sortie):
    """
    Copie les trames AMR de [debut_s, fin_s[ dans un fichier autonome.
    Aucun ré-encodage : les trames sont recopiées telles quelles.
    """
    with open(file_path, 'rb') as f:
        donnees = f.read()

    entete = donnees[:6]
    assert entete == b'#!AMR\n', f'entête AMR-NB inattendue : {entete!r}'

    i = 6
    numero = 0
    trames = []
    while i < len(donnees):
        mode = (donnees[i] >> 3) & 0x0F
        taille = TAILLE_TRAME[mode]
        if taille == 0 or i + taille > len(donnees):
            break
        t = numero * DUREE_TRAME
        if debut_s <= t < fin_s:
            trames.append(donnees[i:i + taille])
        numero += 1
        i += taille

    with open(sortie, 'wb') as f:
        f.write(entete)
        f.writelines(trames)
    return len(trames) * DUREE_TRAME


def transcrire(file_path, model='nova-3', language='multi'):
    with open(file_path, 'rb') as f:
        donnees = f.read()
    reponse = requests.post(
        deepgram_service.base_url,
        params={
            'model': model,
            'language': language,
            'punctuate': 'true',
            'paragraphs': 'true',
            'smart_format': 'true',
            'diarize': 'false',
        },
        headers={
            'Authorization': f'Token {deepgram_service.api_key}',
            'Content-Type': 'audio/amr',
        },
        data=donnees,
        timeout=300,
    )
    if reponse.status_code != 200:
        return None, f'HTTP {reponse.status_code}'
    alt = reponse.json()['results']['channels'][0]['alternatives'][0]
    return alt.get('words', []), None


# (étiquette, fichier, début, fin) — les passages sans aucun mot relevés par le
# diagnostic de couverture.
PASSAGES = [
    ('bruité : trou après 40,6 s', 'audio_test.amr', 40.6, 76.0),
    ('bruité : trou après 298,4 s', 'audio_test.amr', 298.4, 314.5),
    ('bruité : trou après 358,1 s', 'audio_test.amr', 358.1, 374.5),
    ('clair  : trou après 286,7 s', 'audio_test_claire.amr', 286.7, 302.1),
    # Le symptôme exact de la production : la transcription s'arrête à 220 s
    # sur 391 s avec l'ancienne configuration. La queue est-elle récupérable
    # par découpage ? C'est ce qui rendrait la correction auto-réparatrice.
    ('bruité : QUEUE perdue (arrêt à 220 s)', 'audio_test.amr', 220.0, 391.2),
]


def main():
    print('=' * 78)
    print('PASSAGES SANS AUCUN MOT — RÉCUPÉRABLES PAR DÉCOUPAGE ?')
    print('=' * 78)

    for etiquette, nom, debut, fin in PASSAGES:
        chemin = os.path.join(RACINE, nom)
        if not os.path.exists(chemin):
            print(f'\n{etiquette} : fichier absent')
            continue

        sortie = os.path.join(RACINE, '_segment_%s.amr' % os.path.splitext(nom)[0])
        duree = decouper(chemin, debut, fin, sortie)

        mots, erreur = transcrire(sortie)
        print(f'\n{etiquette}  [{debut:.1f} s → {fin:.1f} s, {duree:.1f} s extraits]')
        if erreur:
            print(f'   ERREUR: {erreur}')
            continue
        if mots:
            texte = ' '.join(m.get('punctuated_word') or m.get('word') or '' for m in mots)
            print(f'   ✅ {len(mots)} mots récupérés : {texte.strip()[:150]}')
        else:
            print('   ❌ aucun mot — le passage est réellement inexploitable '
                  '(parole masquée par le bruit)')

        os.remove(sortie)

    print('\n' + '=' * 78)


if __name__ == '__main__':
    sys.exit(main())
