"""
Vérification TACHE ÉTUDIANT — contrôle d'achat sur le lancement QCM.

Règles vérifiées (backend/tache_bug_etudiant.md, point 2) :
  - ETUDIANT abonné QCM SANS achat  → 403 purchase_required
      (génération personnalisée + standard + check)
  - ETUDIANT APRÈS achat completed  → génération autorisée
  - Résumé GRATUIT (sans achat)     → génération autorisée
  - CP (sans achat)                 → génération autorisée

Usage : PYTHONIOENCODING=utf-8 python test_tache_etudiant_check.py
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
import django
django.setup()

from unittest import mock
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from courses.models import Course, Universite, Filiere, Promotion, Summary
from courses.personalized_exercise_views import (
    generate_personalized_exercise_view,
    check_personalized_exercise_exists,
)
from courses.exercise_views import generate_exercise_view
from users.models import UserProfile
from payments.models import Service, Abonnement, Purchase

P = '__TU_'  # préfixe des objets de test


def log(msg):
    print(f'  {msg}')


def cleanup():
    UserProfile.objects.filter(user__username__startswith=P).delete()
    Abonnement.objects.filter(user__username__startswith=P).delete()
    Purchase.objects.filter(user__username__startswith=P).delete()
    User.objects.filter(username__startswith=P).delete()
    Summary.objects.filter(titre__startswith=P).delete()
    Course.objects.filter(nom=f'{P}Cours').delete()
    Promotion.objects.filter(nom=f'{P}Promo').delete()
    Filiere.objects.filter(nom=f'{P}Fil').delete()
    Universite.objects.filter(nom=f'{P}Univ').delete()
    Service.objects.filter(nom=f'{P}QCM').delete()


def make_subscribed_user(username, groupe, u, f, pr, service):
    user = User.objects.create_user(username=username, password='x')
    UserProfile.objects.create(
        user=user, groupe=groupe, universite=u, filiere=f, promotion=pr
    )
    Abonnement.objects.create(
        user=user, service=service, status='active',
        date_debut=timezone.now() - timedelta(days=1),
        date_fin=timezone.now() + timedelta(days=30),
    )
    return user


def main():
    results = []
    factory = APIRequestFactory()

    # ── Setup ──
    u = Universite.objects.create(nom=f'{P}Univ')
    f = Filiere.objects.create(nom=f'{P}Fil')
    pr = Promotion.objects.create(nom=f'{P}Promo')
    course = Course.objects.create(nom=f'{P}Cours', filiere='x', university='x')
    paid = Summary.objects.create(
        titre=f'{P}ResumePayant', texte_resume='Contenu du résumé payant.',
        course=course, author_type='cp', is_validated=True, is_free=False,
    )
    free = Summary.objects.create(
        titre=f'{P}ResumeGratuit', texte_resume='Contenu gratuit.',
        course=course, author_type='cp', is_validated=True, is_free=True,
    )
    service = Service.objects.create(
        nom=f'{P}QCM', description='Test', type='premium', price='5.00',
        currency='USD', duree_mois=1, is_active=True,
    )
    student = make_subscribed_user('__tu_student', 'ETUDIANT', u, f, pr, service)
    cp = make_subscribed_user('__tu_cp', 'CP', u, f, pr, service)
    log(f'Setup: étudiant={student.username}, CP={cp.username}, '
        f'résumé payant={paid.id}, résumé gratuit={free.id}')

    # ── 1. ETUDIANT sans achat : tout est bloqué (403 purchase_required) ──
    with mock.patch('courses.personalized_exercise_views._launch_generation'):
        req = factory.post(
            f'/api/summaries/{paid.id}/personalized-exercise/generate/',
            {'difficulty': 'medium'}, format='json',
        )
        force_authenticate(req, user=student)
        resp = generate_personalized_exercise_view(req, paid.id)
    ok = (resp.status_code == 403
          and resp.data.get('purchase_required') is True
          and resp.data.get('code') == 'purchase_required')
    log(f'[1] Étudiant sans achat, génération personnalisée → '
        f'{resp.status_code} (purchase_required={resp.data.get("purchase_required")})')
    results.append(('403 purchase_required (génération personnalisée)', ok))

    req = factory.post(
        f'/api/summaries/{paid.id}/generate-exercise/',
        {'difficulty': 'medium'}, format='json',
    )
    force_authenticate(req, user=student)
    resp = generate_exercise_view(req, paid.id)
    ok = (resp.status_code == 403
          and resp.data.get('purchase_required') is True)
    log(f'[2] Étudiant sans achat, génération standard → '
        f'{resp.status_code} (purchase_required={resp.data.get("purchase_required")})')
    results.append(('403 purchase_required (génération standard)', ok))

    req = factory.get(f'/api/summaries/{paid.id}/personalized-exercise/check/')
    force_authenticate(req, user=student)
    resp = check_personalized_exercise_exists(req, paid.id)
    ok = (resp.status_code == 403
          and resp.data.get('purchase_required') is True)
    log(f'[3] Étudiant sans achat, check → '
        f'{resp.status_code} (purchase_required={resp.data.get("purchase_required")})')
    results.append(('403 purchase_required (check)', ok))

    # ── 2. APRÈS achat completed : génération autorisée ──
    Purchase.objects.create(
        user=student, summary=paid, amount='5.00',
        payment_method='mobile_money', status='completed',
    )
    with mock.patch('courses.personalized_exercise_views._launch_generation'):
        req = factory.post(
            f'/api/summaries/{paid.id}/personalized-exercise/generate/',
            {'difficulty': 'medium'}, format='json',
        )
        force_authenticate(req, user=student)
        resp = generate_personalized_exercise_view(req, paid.id)
    ok = resp.status_code in (200, 202) and 'purchase_required' not in resp.data
    log(f'[4] Étudiant avec achat, génération personnalisée → {resp.status_code}')
    results.append(('génération personnalisée autorisée après achat', ok))

    with mock.patch('courses.exercise_views.generate_exercises_for_summary'):
        req = factory.post(
            f'/api/summaries/{paid.id}/generate-exercise/',
            {'difficulty': 'medium'}, format='json',
        )
        force_authenticate(req, user=student)
        resp = generate_exercise_view(req, paid.id)
    ok = resp.status_code in (200, 201) and 'purchase_required' not in resp.data
    log(f'[5] Étudiant avec achat, génération standard → {resp.status_code}')
    results.append(('génération standard autorisée après achat', ok))

    # ── 3. Résumé GRATUIT (sans achat) : autorisé ──
    with mock.patch('courses.personalized_exercise_views._launch_generation'):
        req = factory.post(
            f'/api/summaries/{free.id}/personalized-exercise/generate/',
            {'difficulty': 'medium'}, format='json',
        )
        force_authenticate(req, user=student)
        resp = generate_personalized_exercise_view(req, free.id)
    ok = resp.status_code in (200, 202)
    log(f'[6] Résumé gratuit, génération personnalisée → {resp.status_code}')
    results.append(('résumé gratuit non bloqué', ok))

    # ── 4. CP (sans achat) : autorisé ──
    with mock.patch('courses.personalized_exercise_views._launch_generation'):
        req = factory.post(
            f'/api/summaries/{paid.id}/personalized-exercise/generate/',
            {'difficulty': 'medium'}, format='json',
        )
        force_authenticate(req, user=cp)
        resp = generate_personalized_exercise_view(req, paid.id)
    ok = resp.status_code in (200, 202)
    log(f'[7] CP sans achat, génération personnalisée → {resp.status_code}')
    results.append(('CP non bloqué', ok))

    cleanup()
    log('Cleanup OK')

    # ── Bilan ──
    print()
    failed = [name for name, ok in results if not ok]
    for name, ok in results:
        print(f'{"✅" if ok else "❌"} {name}')
    if failed:
        print(f'\nÉCHEC: {len(failed)} vérification(s)')
        sys.exit(1)
    print('\nOK TACHE ÉTUDIANT — contrôle d\'achat QCM vérifié')


if __name__ == '__main__':
    cleanup()
    main()
