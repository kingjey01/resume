"""
Diagnostic tâche 36 — où et pourquoi la transcription s'arrête-t-elle ?

Ne se contente pas de comparer la fin du dernier mot à la durée : mesure aussi
les TROUS de la timeline (un arrêt net et un passage perdu au milieu ne se
soignent pas de la même façon) et relève pour chaque appel le `request_id` et
le modèle réellement utilisé par Deepgram (`metadata.model_info`), afin de
pouvoir confronter le résultat aux journaux côté Deepgram.

Usage (depuis backend/) :
    .venv/Scripts/python.exe diagnostic_tache36_couverture.py
"""

import os
import sys

import django
import requests

# La console Windows est en cp1252 : sans cela, les caractères accentués et les
# encadrés font planter le script (le même piège avait déjà cassé
# `test_tache3_check.py`).
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from courses.deepgram_service import deepgram_service  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIERS = [
    ('clair ', os.path.join(RACINE, 'audio_test_claire.amr')),
    ('bruité', os.path.join(RACINE, 'audio_test.amr')),
]

# (modèle, langue, étiquette)
CONFIGS = [
    ('nova-3', 'multi', 'ACTUEL  (code non déployé)'),
    ('nova-2', 'fr', "DÉPLOYÉ (état HEAD)"),
    ('nova-3', 'fr', 'intermédiaire'),
]

SEUIL_TROU = 15.0  # secondes : au-delà, c'est un passage réellement perdu


def interroger(file_path, model, language):
    """Appel Deepgram brut, mêmes paramètres que la production."""
    with open(file_path, 'rb') as f:
        donnees = f.read()

    params = {
        'model': model,
        'language': language,
        'punctuate': 'true',
        'paragraphs': 'true',
        'smart_format': 'true',
        'diarize': 'false',
    }
    reponse = requests.post(
        deepgram_service.base_url,
        params=params,
        headers={
            'Authorization': f'Token {deepgram_service.api_key}',
            'Content-Type': deepgram_service._get_mime_type(file_path),
        },
        data=donnees,
        timeout=deepgram_service._adaptive_timeout(file_path, len(donnees)),
    )
    if reponse.status_code != 200:
        return {'erreur': f'HTTP {reponse.status_code} — {reponse.text[:200]}'}

    resultat = reponse.json()
    alternatives = resultat['results']['channels'][0]['alternatives'][0]
    mots = alternatives.get('words', [])
    meta = resultat.get('metadata', {}) or {}

    duree = float(meta.get('duration') or 0)
    fin = float(mots[-1].get('end') or 0) if mots else 0.0
    couverture = (fin / duree * 100) if duree else 0.0

    # Trous entre mots consécutifs : distingue « arrêt net » de « passage perdu ».
    trous = []
    for precedent, suivant in zip(mots, mots[1:]):
        ecart = float(suivant.get('start') or 0) - float(precedent.get('end') or 0)
        if ecart >= SEUIL_TROU:
            trous.append((float(precedent.get('end') or 0), ecart))

    return {
        'duree': duree,
        'mots': len(mots),
        'fin': fin,
        'couverture': couverture,
        'manquantes': max(0.0, duree - fin),
        'trous': trous,
        'modele_reel': str(meta.get('model_info') or {}),
        'request_id': meta.get('request_id'),
        'transcript': alternatives.get('transcript', ''),
    }


def main():
    print('=' * 78)
    print('COUVERTURE DE LA TRANSCRIPTION — diagnostic tâche 36')
    print('=' * 78)

    for etiquette, chemin in FICHIERS:
        if not os.path.exists(chemin):
            print(f'\n{etiquette} : fichier absent ({chemin})')
            continue
        print(f'\n{"=" * 78}\nAUDIO {etiquette.upper()} — {os.path.basename(chemin)} '
              f'({os.path.getsize(chemin) / 1024:.0f} Ko)\n{"=" * 78}')

        for model, language, libelle in CONFIGS:
            print(f'\n  ── {model} + language={language}  [{libelle}]')
            try:
                r = interroger(chemin, model, language)
            except Exception as e:  # réseau, timeout…
                print(f'     ERREUR: {type(e).__name__}: {e}')
                continue

            if 'erreur' in r:
                print(f'     {r["erreur"]}')
                continue

            print(f'     durée lue      : {r["duree"]:.1f} s')
            print(f'     mots transcrits: {r["mots"]}')
            print(f'     dernier mot à  : {r["fin"]:.1f} s')
            print(f'     COUVERTURE     : {r["couverture"]:.1f} %  '
                  f'({r["manquantes"]:.0f} s manquantes)')
            print(f'     modèle réel    : {r["modele_reel"]}')
            print(f'     request_id     : {r["request_id"]}')
            if r['trous']:
                for debut, ecart in r['trous']:
                    print(f'     ⚠️ TROU de {ecart:.1f} s après {debut:.1f} s')
            else:
                print('     aucun trou >= %.0f s' % SEUIL_TROU)
            queue = r['transcript'].strip()[-90:]
            print(f'     fin du texte   : …{queue}')

    print('\n' + '=' * 78)


if __name__ == '__main__':
    sys.exit(main())
