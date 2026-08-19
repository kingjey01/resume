"""
Vérification des correctifs TACHE3 :
1. Compilation des fichiers modifiés
2. Fallback standard : questions construites depuis le contenu réel (aucune question générique)
3. Vue personnalisée : changement de niveau → régénération automatique
"""
import os
import django
import py_compile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

FILES = [
    'courses/exercise_generator.py',
    'courses/personalized_exercise_generator.py',
    'courses/personalized_exercise_views.py',
]

# ═══ 1. Compilation ═══
print("═══ 1. COMPILATION ═══")
for f in FILES:
    py_compile.compile(f, doraise=True)
    print(f"  ✓ {f} compile")

# ═══ 2. Fallback standard ═══
print("\n═══ 2. FALLBACK STANDARD (contenu réel) ═══")
from courses.exercise_generator import ExerciseGenerator

RESUME = """La programmation orientée objet en Python repose sur la notion de classe qui permet de regrouper des données et des fonctions.
Une classe est définie par le mot-clé class et son constructeur __init__ initialise les attributs de l'instance.
L'héritage permet à une classe fille de réutiliser les méthodes de sa classe mère, par exemple class Chien(Animal).
Le polymorphisme désigne la capacité d'un objet à adapter son comportement selon sa classe réelle.
Les méthodes magiques comme __str__ et __eq__ personnalisent l'affichage et la comparaison des objets.
```python
class Chien(Animal):
    def parler(self):
        return "Wouf"
```
Le principe d'encapsulation recommande de protéger les attributs privés avec un underscore.
Une variable de classe est partagée par toutes les instances, tandis qu'une variable d'instance appartient à chaque objet.
Le garbage collector libère automatiquement la mémoire des objets devenus inutiles.
"""

gen = ExerciseGenerator()
questions = gen._generate_mock_questions('Programmation Python', RESUME, difficulty='medium')
print(f"  Questions générées: {len(questions)}")
assert 4 <= len(questions) <= 8, f"Attendu 4-8 questions, obtenu {len(questions)}"

GENERIC = ['objectif principal', 'domaine principal', 'compétence', 'niveau de difficulté',
           'pourquoi est-il important', 'concept a', 'concept b', 'option a', 'réponse a']
ok = True
for q in questions:
    text = q['question'].lower()
    opts = ' '.join(str(v).lower() for v in q['options'].values())
    for g in GENERIC:
        assert g not in text and g not in opts, f"Question générique détectée: « {q['question']} » (contenu: {g})"
    assert len(q['options']) == 4 and q['correct_answer'] in 'ABCD'
    # Chaque option doit être liée au contenu réel
    for opt in q['options'].values():
        assert len(str(opt).strip()) >= 3, f"Option trop courte: {opt}"
print(f"  ✓ {len(questions)} questions toutes construites depuis le contenu réel, aucune générique")

# Vérifier que les extraits de code produisent bien code_language/code_block
code_qs = [q for q in questions if q.get('code_block')]
print(f"  Questions avec code: {len(code_qs)}")
if code_qs:
    assert code_qs[0]['code_language'], "code_language manquant"
    assert 'class Chien' in code_qs[0]['code_block'], "code_block ne contient pas le vrai code"

# ═══ 3. Vue personnalisée : changement de niveau ═══
print("\n═══ 3. VUE PERSONNALISÉE (niveau Moyen → Facile) ═══")
from unittest import mock
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from django.contrib.auth.models import User
from courses.models import Course, Universite, Filiere, Promotion, Summary, UserPersonalizedExercise, UserPersonalizedQuestion
from courses.personalized_exercise_views import (
    generate_personalized_exercise_view,
    check_personalized_exercise_exists,
    submit_personalized_exercise_view,
    get_personalized_attempts_view,
    get_personalized_attempt_detail_view,
)
from users.models import UserProfile
from payments.models import Service, Abonnement, Purchase
from django.utils import timezone
from datetime import timedelta

# Nettoyage préalable (le script est réutilisable)
UserPersonalizedExercise.objects.filter(summary__titre__startswith='__T3_').delete()
Summary.objects.filter(titre__startswith='__T3_').delete()
Course.objects.filter(nom='__T3_Cours').delete()
Promotion.objects.filter(nom='__T3_Promo').delete()
Filiere.objects.filter(nom='__T3_Fil').delete()
Universite.objects.filter(nom='__T3_Univ').delete()
Abonnement.objects.filter(user__username='__t3_user').delete()
Service.objects.filter(nom='QCM Exercices').delete()
UserProfile.objects.filter(user__username='__t3_user').delete()
User.objects.filter(username='__t3_user').delete()

# Préparer les données
u = Universite.objects.create(nom='__T3_Univ')
f = Filiere.objects.create(nom='__T3_Fil')
p = Promotion.objects.create(nom='__T3_Promo')
c = Course.objects.create(nom='__T3_Cours', filiere='x', university='x')
s = Summary.objects.create(titre='__T3_Resume', texte_resume=RESUME, course=c, author_type='cp', is_validated=True)
user = User.objects.create_user(username='__t3_user', password='x')

# Profil + abonnement actif requis par la permission HasActiveSubscription
UserProfile.objects.create(user=user, universite=u, filiere=f, promotion=p)
service = Service.objects.create(nom='QCM Exercices', description='Test', type='premium', price='5.00', currency='USD', duree_mois=1, is_active=True)
Abonnement.objects.create(
    user=user, service=service, status='active',
    date_debut=timezone.now() - timedelta(days=1),
    date_fin=timezone.now() + timedelta(days=30),
)
# Achat 'completed' requis par le nouveau contrôle d'accès QCM
# (un résumé payant ne génère un QCM que s'il a été acheté)
Purchase.objects.create(
    user=user, summary=s, amount='5.00',
    payment_method='mobile_money', status='completed',
)

factory = APIRequestFactory()

with mock.patch('courses.personalized_exercise_views.has_exercise_subscription', return_value=True), \
     mock.patch('courses.personalized_exercise_views._launch_generation') as launch:

    # 3a. Génération initiale en Moyen
    req = factory.post(f'/api/exercises/{s.id}/generate/', {'difficulty': 'medium'}, format='json')
    force_authenticate(req, user=user)
    resp = generate_personalized_exercise_view(req, s.id)
    print(f"  3a. 1ère génération (Moyen): status={resp.status_code}, difficulty={resp.data.get('difficulty')}")
    assert resp.status_code == 202 and resp.data['difficulty'] == 'medium'

    # L'exercice Moyen existe maintenant
    med_ex = UserPersonalizedExercise.objects.get(user=user, summary=s, difficulty='medium')
    med_ex.status = 'completed'
    med_ex.save()
    print(f"  Exercice Moyen: id={med_ex.id}, difficulty={med_ex.difficulty}, status={med_ex.status}")

    # 3b. Demande Facile SANS regenerate → NOUVEL exercice distinct (pas d'écrasement)
    launch.reset_mock()
    req = factory.post(f'/api/exercises/{s.id}/generate/', {'difficulty': 'easy'}, format='json')
    force_authenticate(req, user=user)
    resp = generate_personalized_exercise_view(req, s.id)
    print(f"  3b. Génération Facile: status={resp.status_code}, difficulty={resp.data.get('difficulty')}")
    assert resp.status_code == 202, f"Attendu 202, obtenu {resp.status_code}: {resp.data}"
    assert resp.data['difficulty'] == 'easy'
    assert launch.called, "La génération doit être lancée pour un niveau inexistant"
    args, _ = launch.call_args
    assert args[3] == 'easy', f"Génération lancée avec {args[3]} au lieu de easy"

    easy_ex = UserPersonalizedExercise.objects.get(user=user, summary=s, difficulty='easy')
    assert easy_ex.id != med_ex.id, "Facile doit créer un exercice SÉPARÉ, pas écraser le Moyen"
    med_ex.refresh_from_db()
    assert med_ex.difficulty == 'medium' and med_ex.status == 'completed', \
        "L'exercice Moyen ne doit pas être modifié par la génération Facile"
    assert UserPersonalizedExercise.objects.filter(user=user, summary=s).count() == 2

    # 3c. Demande Difficile → 3ème exercice distinct (plus jamais les questions Moyennes)
    launch.reset_mock()
    req = factory.post(f'/api/exercises/{s.id}/generate/', {'difficulty': 'hard'}, format='json')
    force_authenticate(req, user=user)
    resp = generate_personalized_exercise_view(req, s.id)
    print(f"  3c. Génération Difficile: status={resp.status_code}, difficulty={resp.data.get('difficulty')}")
    assert resp.status_code == 202 and resp.data['difficulty'] == 'hard'
    hard_ex = UserPersonalizedExercise.objects.get(user=user, summary=s, difficulty='hard')
    assert len({med_ex.id, easy_ex.id, hard_ex.id}) == 3, "3 exercices distincts attendus"
    assert UserPersonalizedExercise.objects.filter(user=user, summary=s).count() == 3

    # 3d. Même niveau + completed → retourne l'existant sans régénérer
    launch.reset_mock()
    easy_ex.status = 'completed'
    easy_ex.save()
    req = factory.post(f'/api/exercises/{s.id}/generate/', {'difficulty': 'easy'}, format='json')
    force_authenticate(req, user=user)
    resp = generate_personalized_exercise_view(req, s.id)
    print(f"  3d. Même niveau (easy, completed): status={resp.status_code}, exercise_id={resp.data.get('exercise_id')}")
    assert resp.status_code == 200 and resp.data['status'] == 'completed'
    assert resp.data['exercise_id'] == easy_ex.id
    assert not launch.called, "Aucune régénération si le niveau est identique"

    # 3e. check : sans difficulty → dernier créé ; avec difficulty → le niveau demandé
    req = factory.get(f'/api/exercises/{s.id}/personalized-exercise/check/')
    force_authenticate(req, user=user)
    resp = check_personalized_exercise_exists(req, s.id)
    print(f"  3e. check sans difficulty: exists={resp.data.get('exists')}, difficulty={resp.data.get('difficulty')}")
    assert resp.data['exists'] and resp.data['difficulty'] == 'hard'

    req = factory.get(f'/api/exercises/{s.id}/personalized-exercise/check/?difficulty=easy')
    force_authenticate(req, user=user)
    resp = check_personalized_exercise_exists(req, s.id)
    print(f"  3e. check difficulty=easy: exercise_id={resp.data.get('exercise_id')}")
    assert resp.data['exists'] and resp.data['exercise_id'] == easy_ex.id

# ═══ 4. Isolation des tentatives par niveau ═══
print("\n═══ 4. ISOLATION DES TENTATIVES PAR NIVEAU ═══")

# Compléter les 3 exercices avec des questions propres à chaque niveau
questions_facile = [
    {'question_text': 'F1 — Quel mot-clé définit une classe en Python ?', 'options': {'A': 'class', 'B': 'def', 'C': 'import', 'D': 'return'}, 'correct_answer': 'A', 'explanation': 'Le mot-clé class définit une classe.'},
    {'question_text': 'F2 — Comment s\'appelle le constructeur Python ?', 'options': {'A': '__init__', 'B': '__new__', 'C': 'construct', 'D': 'init'}, 'correct_answer': 'A', 'explanation': '__init__ initialise l\'instance.'},
]
questions_moyen = [
    {'question_text': 'M1 — Quelle classe hérite de Animal ?', 'options': {'A': 'Chien', 'B': 'Chat', 'C': 'Oiseau', 'D': 'Poisson'}, 'correct_answer': 'A', 'explanation': 'class Chien(Animal).'},
    {'question_text': 'M2 — Que désigne le polymorphisme ?', 'options': {'A': 'Adapter le comportement selon la classe réelle', 'B': 'Créer une classe', 'C': 'Détruire un objet', 'D': 'Hériter d\'une classe'}, 'correct_answer': 'A', 'explanation': 'Capacité d\'adapter le comportement.'},
]
questions_difficile = [
    {'question_text': 'H1 — Pourquoi encapsuler les attributs privés ?', 'options': {'A': 'Les protéger avec un underscore', 'B': 'Pour rien', 'C': 'Accélérer le code', 'D': 'Supprimer la classe'}, 'correct_answer': 'A', 'explanation': 'Le principe d\'encapsulation.'},
    {'question_text': 'H2 — À quoi sert le garbage collector ?', 'options': {'A': 'Libérer la mémoire des objets inutiles', 'B': 'Compiler le code', 'C': 'Trier les objets', 'D': 'Gérer le réseau'}, 'correct_answer': 'A', 'explanation': 'Libère automatiquement la mémoire.'},
]
def set_questions(ex, qs):
    """Structure 3 tables : chaque question = ligne UserPersonalizedQuestion."""
    ex.questions.all().delete()
    UserPersonalizedQuestion.objects.bulk_create([
        UserPersonalizedQuestion(
            personalized_exercise=ex,
            question_text=q['question_text'],
            options=q['options'],
            correct_answer=q['correct_answer'],
            explanation=q['explanation'],
            order=i,
        )
        for i, q in enumerate(qs)
    ])
    ex.status = 'completed'
    ex.save()


set_questions(med_ex, questions_moyen)
set_questions(easy_ex, questions_facile)
set_questions(hard_ex, questions_difficile)
# Vérifier que les questions sont bien des lignes séparées (3 tables)
assert UserPersonalizedQuestion.objects.filter(personalized_exercise__in=[easy_ex, med_ex, hard_ex]).count() == 6
print("  Les 6 questions sont stockées en lignes séparées (table UserPersonalizedQuestion)")

# Soumettre une tentative par niveau
attempt_ids = {}
for label, ex_obj, qs in [
    ('Facile', easy_ex, questions_facile),
    ('Moyen', med_ex, questions_moyen),
    ('Difficile', hard_ex, questions_difficile),
]:
    answers = {str(i): 'A' for i in range(len(qs))}
    req = factory.post(f'/api/exercises/{ex_obj.id}/submit/', {'answers': answers}, format='json')
    force_authenticate(req, user=user)
    resp = submit_personalized_exercise_view(req, ex_obj.id)
    print(f"  4a. Tentative {label}: status={resp.status_code}, score={resp.data.get('score')}")
    assert resp.status_code == 200
    # Les questions renvoyées DOIVENT être uniquement celles du niveau soumis
    texts = [r['question_text'] for r in resp.data['results']]
    assert all(texts[i].startswith(qs[i]['question_text'][0]) for i in range(len(qs))), \
        f"Tentative {label}: mélange de questions détecté: {texts}"
    attempt_ids[label] = resp.data['attempt_id']

# Historique : chaque tentative affiche SON niveau (Facile, Moyen, Difficile)
req = factory.get('/api/exercises/personalized-exercises/attempts/', {'summary_id': s.id})
force_authenticate(req, user=user)
resp = get_personalized_attempts_view(req)
print(f"  4b. Historique: {sorted(a['difficulty_label'] for a in resp.data['attempts'])}")
labels = sorted(a['difficulty_label'] for a in resp.data['attempts'])
assert labels == ['Difficile', 'Facile', 'Moyen'], f"Attendu Facile/Moyen/Difficile, obtenu {labels}"
for a in resp.data['attempts']:
    if a['difficulty'] == 'easy':
        assert a['exercise_id'] == easy_ex.id, "La tentative Facile doit pointer l'exercice Facile"
    if a['difficulty'] == 'hard':
        assert a['exercise_id'] == hard_ex.id, "La tentative Difficile doit pointer l'exercice Difficile"

# Détail d'une tentative : le niveau affiché = niveau de l'exercice de la tentative
req = factory.get(f'/api/exercises/personalized-exercises/attempts/{attempt_ids["Facile"]}/')
force_authenticate(req, user=user)
resp = get_personalized_attempt_detail_view(req, attempt_ids['Facile'])
print(f"  4c. Détail tentative Facile: difficulty={resp.data['exercise']['difficulty']}")
assert resp.data['exercise']['difficulty'] == 'easy'
assert all(r['question_text'].startswith('F') for r in resp.data['results'])

print("\n✅ TOUS LES TESTS TACHE3 PASSENT")

# Nettoyage
user.delete()
s.delete()
c.delete()
p.delete()
f.delete()
u.delete()
service.delete()
