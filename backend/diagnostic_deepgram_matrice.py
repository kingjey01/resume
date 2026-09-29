"""
DIAGNOSTIC TACHE 33 -- Matrice de parametres Deepgram sur l'audio bruite.

But : determiner QUELLE configuration fait couvrir a Deepgram la totalite
du fichier bruite (audio_test.amr), au lieu de s'arreter a ~220s / 391s.

Ce script N'ECRIT RIEN en base et ne modifie AUCUN fichier : il se contente
d'appeler l'API avec differents jeux de parametres et de comparer.
"""

import os
import sys
import time

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import requests  # noqa: E402
from courses.deepgram_service import deepgram_service  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(RACINE, 'audio_test.amr')
SEP = '=' * 78

# Jeux de parametres a comparer. Tous gardent les reglages actuels du service
# (punctuate / smart_format) pour ne mesurer que l'effet des options ajoutees.
CAS = [
    ('A. actuel           nova-2, fr, diarize=false',
     {'model': 'nova-2', 'language': 'fr', 'punctuate': 'true',
      'smart_format': 'true', 'diarize': 'false'}),
    ('B. diarize=true     nova-2, fr',
     {'model': 'nova-2', 'language': 'fr', 'punctuate': 'true',
      'smart_format': 'true', 'diarize': 'true'}),
    ('C. nova-3           fr, diarize=false',
     {'model': 'nova-3', 'language': 'fr', 'punctuate': 'true',
      'smart_format': 'true', 'diarize': 'false'}),
    ('D. nova-3           fr, diarize=true',
     {'model': 'nova-3', 'language': 'fr', 'punctuate': 'true',
      'smart_format': 'true', 'diarize': 'true'}),
    ('E. nova-3           multi, diarize=true',
     {'model': 'nova-3', 'language': 'multi', 'punctuate': 'true',
      'smart_format': 'true', 'diarize': 'true'}),
    ('F. nova-2 fr + utterances + diarize',
     {'model': 'nova-2', 'language': 'fr', 'punctuate': 'true',
      'smart_format': 'true', 'diarize': 'true', 'utterances': 'true'}),
]


def mesurer(label, params):
    mime = deepgram_service._get_mime_type(AUDIO)
    with open(AUDIO, 'rb') as f:
        data = f.read()

    t0 = time.time()
    try:
        r = requests.post(
            deepgram_service.base_url, params=params,
            headers={'Authorization': f'Token {deepgram_service.api_key}',
                     'Content-Type': mime},
            data=data, timeout=1800,
        )
    except Exception as e:
        print(f"  [ECHEC reseau] {e}")
        return None
    duree = time.time() - t0

    print(f"\n--- {label}")
    if r.status_code != 200:
        print(f"  [ECHEC] HTTP {r.status_code} : {r.text[:300]}")
        return None

    d = r.json()
    meta = d.get('metadata') or {}
    alts = (d.get('results') or {}).get('channels') or [{}]
    alt = (alts[0].get('alternatives') or [{}])[0]
    mots = alt.get('words') or []
    tr = alt.get('transcript') or ''
    duree_audio = meta.get('duration')
    fin = mots[-1].get('end') if mots else None

    couv = (fin / duree_audio * 100) if (fin and duree_audio) else 0
    print(f"  appel={duree:5.1f}s  duree_audio={duree_audio}  mots={len(mots):5d}  "
          f"fin={fin}  couverture={couv:.1f}%  car={len(tr)}")
    if couv < 95:
        print(f"  >>> INCOMPLET : il manque {duree_audio - fin:.0f}s")
    else:
        print(f"  >>> COMPLET")
    return {'couv': couv, 'mots': len(mots), 'fin': fin, 'car': len(tr)}


def main():
    print(SEP)
    print("MATRICE DE PARAMETRES DEEPGRAM -- audio_test.amr (bruite)")
    print(SEP)
    if not deepgram_service.is_configured():
        print("[ERREUR] DEEPGRAM_API_KEY non configuree")
        return
    if not os.path.exists(AUDIO):
        print(f"[ERREUR] introuvable : {AUDIO}")
        return

    resultats = {}
    for label, params in CAS:
        res = mesurer(label, params)
        if res:
            resultats[label] = res

    print(f"\n{SEP}\nSYNTHESE\n{SEP}")
    for label, res in sorted(resultats.items(), key=lambda kv: -kv[1]['couv']):
        print(f"  {res['couv']:6.1f}%  {res['mots']:5d} mots  {label}")


if __name__ == '__main__':
    main()
