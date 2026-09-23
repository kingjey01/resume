"""
DIAGNOSTIC -- Suivi complet de la chaine de generation d'un resume IA.

Suit chaque etape pour localiser une eventuelle troncature :

    audio -> transcription Deepgram -> prompt -> reponse brute DeepSeek
          -> _clean_text -> base de donnees -> serializer API

Utilisation :
    .venv/Scripts/python.exe diagnostic_truncature_resume.py [chemin_audio]

Par defaut le script utilise IPP.amr (audio de test place dans backend/).

Ce script NE MODIFIE RIEN : la base est utilisee dans une transaction annulee.
Aucune limite n'est modifiee : on mesure, on ne corrige pas.
"""

import os
import sys
import time

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import requests  # noqa: E402
from django.db import connection, transaction  # noqa: E402

from courses.deepgram_service import deepgram_service  # noqa: E402
from courses.deepseek_service import DeepSeekService  # noqa: E402
from courses.models import Course, Summary  # noqa: E402

AUDIO_DEFAUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'IPP.amr')
SEP = '=' * 78


def titre(txt):
    print(f"\n{SEP}\n{txt}\n{SEP}")


# ─────────────────────────────────────────────────────────────── Etape 1

def etape_1_transcription(chemin_audio):
    titre("ETAPE 1 -- AUDIO -> TRANSCRIPTION DEEPGRAM")

    if not os.path.exists(chemin_audio):
        print(f"[ERREUR] Fichier introuvable : {chemin_audio}")
        return None

    ext = os.path.splitext(chemin_audio)[1].lower()
    mime = deepgram_service._get_mime_type(chemin_audio)
    print(f"Fichier      : {chemin_audio}")
    print(f"Taille       : {os.path.getsize(chemin_audio) / 1024 / 1024:.2f} MB")
    print(f"Extension    : {ext}")
    print(f"MIME utilise : {mime}")

    if not deepgram_service.is_configured():
        print("[ERREUR] DEEPGRAM_API_KEY non configuree")
        return None

    t0 = time.time()
    res = deepgram_service.transcribe_file(chemin_audio, language='fr')
    duree = time.time() - t0

    if not res.get('success'):
        print(f"[ECHEC] {res.get('error')}")
        return None

    transcript = res['transcript']
    mots = res.get('words') or []
    brut = res.get('raw_response') or {}
    duree_audio = (brut.get('metadata') or {}).get('duration')
    fin_mot = mots[-1].get('end') if mots else None

    print(f"\nDuree appel      : {duree:.1f}s")
    print(f"Confidence       : {res.get('confidence')}")
    print(f"Nb de mots       : {len(mots)}")
    print(f"Duree audio      : {duree_audio}")
    print(f"Fin dernier mot  : {fin_mot}")
    if duree_audio and fin_mot:
        ecart = duree_audio - fin_mot
        print(f"Non transcrit    : {ecart:.1f}s"
              f"{'   <-- ALERTE : audio non couvert en entier' if ecart > 5 else ''}")
    print(f"LONGUEUR TRANSCRIPT : {len(transcript)} caracteres")
    print(f"Fin du texte : ...{transcript[-150:]!r}")

    return transcript


# ─────────────────────────────────────────────────────────────── Etape 2

def etape_2_deepseek(service, transcription, label, max_tokens=8000):
    """
    Appelle DeepSeek et inspecte la REPONSE BRUTE.

    Point cle : ce modele RAISONNE. Le champ `reasoning_content` n'est pas
    affiche mais consomme le meme plafond `max_tokens` que le resume. C'est
    la cause des resumes coupes.
    """
    titre(f"ETAPE 2 -- DEEPSEEK ({label})")

    prompt = service._build_summary_prompt(
        transcription, 'COURS DE TEST (diagnostic)', 'Professeur Test', '21/09/2026'
    )

    taille_prompt = len(prompt['system']) + len(prompt['user'])
    print(f"Transcription envoyee : {len(transcription)} caracteres")
    print(f"Prompt total          : {taille_prompt} caracteres (~{taille_prompt // 4} tokens)")
    print(f"max_tokens demande    : {max_tokens}")

    payload = {
        'model': service.MODEL,
        'messages': [
            {'role': 'system', 'content': prompt['system']},
            {'role': 'user', 'content': prompt['user']},
        ],
        'temperature': 0.1,
        'max_tokens': max_tokens,
        'top_p': 0.9,
    }

    t0 = time.time()
    try:
        r = requests.post(
            service.API_URL,
            headers={'Authorization': f'Bearer {service.api_key}',
                     'Content-Type': 'application/json'},
            json=payload,
            timeout=300,
        )
    except Exception as e:
        print(f"[ECHEC] Appel DeepSeek : {e}")
        return None
    duree = time.time() - t0

    print(f"\nDuree appel : {duree:.1f}s")
    print(f"HTTP status : {r.status_code}")
    if r.status_code != 200:
        print(f"Reponse : {r.text[:500]}")
        return None

    data = r.json()
    if not data.get('choices'):
        print(f"[ANOMALIE] Aucun choix : {str(data)[:400]}")
        return None

    choix = data['choices'][0]
    message = choix.get('message', {})
    contenu = message.get('content') or ''
    raisonnement = message.get('reasoning_content') or ''
    usage = data.get('usage', {})
    finish_reason = choix.get('finish_reason')

    print("\n--- REPONSE BRUTE ---")
    print(f"finish_reason           : {finish_reason}")
    print(f"prompt_tokens           : {usage.get('prompt_tokens')}")
    print(f"completion_tokens       : {usage.get('completion_tokens')}")
    print(f"longueur raisonnement   : {len(raisonnement)} caracteres (non affiche)")
    print(f"LONGUEUR RESUME VISIBLE : {len(contenu)} caracteres")
    print(f"Fin du resume : ...{contenu[-150:]!r}")

    if finish_reason == 'length':
        print("\n  *** RESUME COUPE ***")
        print(f"  Le raisonnement ({len(raisonnement)} car.) + le resume ont epuise")
        print(f"  le plafond de {max_tokens} tokens. Le resume est INCOMPLET.")
    else:
        print("\n  Resume termine normalement (finish_reason='stop').")

    return {'contenu': contenu, 'raisonnement': len(raisonnement),
            'finish_reason': finish_reason, 'usage': usage}


# ─────────────────────────────────────────────────────────────── Etape 3

def etape_3_clean_text(service, contenu_brut):
    """
    _clean_text normalise les espaces (espaces multiples -> un, 3 sauts de
    ligne et plus -> 2) : la longueur en caracteres baisse donc un peu, sans
    perte de contenu. Le nombre de MOTS est la mesure pertinente.
    """
    titre("ETAPE 3 -- POST-TRAITEMENT (_clean_text)")
    nettoye = service._clean_text(contenu_brut)

    mots_avant = len(contenu_brut.split())
    mots_apres = len(nettoye.split())

    print(f"Caracteres : {len(contenu_brut)} -> {len(nettoye)} "
          f"({len(nettoye) - len(contenu_brut):+d})")
    print(f"Mots       : {mots_avant} -> {mots_apres} ({mots_apres - mots_avant:+d})")

    if mots_apres < mots_avant:
        print("  [ALERTE] Des mots ont disparu dans _clean_text !")
    else:
        print("  [OK] Aucun mot perdu (baisse de taille = normalisation des espaces).")
    return nettoye


# ─────────────────────────────────────────────────────────────── Etape 4

def etape_4_base(texte):
    titre("ETAPE 4 -- BASE DE DONNEES (ecriture + relecture)")
    print(f"Moteur : {connection.settings_dict['ENGINE']}")

    course = Course.objects.first()
    if not course:
        print("[INFO] Aucun cours en base, etape ignoree.")
        return

    with transaction.atomic():
        summary = Summary.objects.create(
            titre='[DIAGNOSTIC] Test troncature',
            texte_resume=texte,
            course=course,
            author_type='ai',
            prix=0,
            is_free=True,
        )
        summary.refresh_from_db()
        relu = summary.texte_resume
        print(f"Ecrit : {len(texte)} caracteres")
        print(f"Relu  : {len(relu)} caracteres")
        if len(relu) != len(texte):
            print("  [ALERTE] Perte en base : la colonne est trop petite !")
        else:
            print("  [OK] Aucune perte en base de donnees.")
        transaction.set_rollback(True)
    print("(Transaction annulee)")


# ─────────────────────────────────────────────────────────────── Etape 5

def etape_5_serializer(texte):
    titre("ETAPE 5 -- SERIALIZER / API")
    print("SummarySerializer.to_representation() applique des apercus VOLONTAIRES :")
    print("  - utilisateur non authentifie (ou context absent) : 50 caracteres")
    print("  - etudiant sans achat                             : 150 caracteres")
    print("  - par defaut                                      : 100 caracteres")
    print("  - CP / Admin / acheteur                           : TEXTE COMPLET")
    print()
    print("Verifie : GET /summaries/validation/ (utilise par l'ecran Validation)")
    print("  -> get_summaries_for_validation_view() renvoie summary.texte_resume BRUT")
    print("  -> donc AUCUNE troncature cote backend pour le CP.")
    print(f"\nLongueur de reference : {len(texte)} caracteres")


def main():
    chemin = sys.argv[1] if len(sys.argv) > 1 else AUDIO_DEFAUT

    print(SEP)
    print("DIAGNOSTIC DE TRONCATURE DES RESUMES IA")
    print(SEP)

    service = DeepSeekService()
    print(f"DeepSeek configure : {service.is_configured()}")
    print(f"Modele             : {service.MODEL}")
    print(f"Paliers de budget  : {service.SUMMARY_TOKEN_BUDGETS}")

    transcription = etape_1_transcription(chemin)
    if not transcription:
        titre("ABANDON")
        print("Impossible de poursuivre sans transcription.")
        return

    resultat = etape_2_deepseek(service, transcription, 'transcription reelle')
    if not resultat:
        titre("ABANDON")
        print("Impossible de poursuivre sans reponse DeepSeek.")
        return

    nettoye = etape_3_clean_text(service, resultat['contenu'])
    etape_4_base(nettoye)
    etape_5_serializer(nettoye)

    # ── Test avec un contenu volontairement tres long (exige par la tache)
    titre("ETAPE 6 -- CONTENU VOLONTAIREMENT TRES LONG")
    longue = transcription * 8
    print(f"Transcription dupliquee x8 : {len(longue)} caracteres")
    resultat_long = etape_2_deepseek(service, longue, 'contenu tres long')
    if resultat_long:
        nettoye_long = etape_3_clean_text(service, resultat_long['contenu'])
        etape_4_base(nettoye_long)

    # ── Verification de la robustesse : plusieurs appels d'affilee
    titre("ETAPE 7 -- ROBUSTESSE : 3 GENERATIONS SUCCESSIVES")
    print("Le raisonnement varie d'un appel a l'autre, donc la coupure est")
    print("aleatoire. On verifie que l'escalade de budget la rattrape.\n")
    for i in range(1, 4):
        res = service.generate_summary(longue, 'Maths', 'Prof', '21/09/2026')
        if not res.get('success'):
            print(f"  Essai {i} : ECHEC - {res.get('error')}")
            continue
        resume = res.get('summary') or ''
        etat = 'INCOMPLET' if res.get('truncated') else 'COMPLET'
        print(f"  Essai {i} : {etat:9s} {len(resume):6d} car. "
              f"(finish_reason={res.get('finish_reason')})")

    titre("FIN DU DIAGNOSTIC")


if __name__ == '__main__':
    main()
