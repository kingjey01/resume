"""
Tests des statistiques métier et financières (app analytics).

Couvre :
- restriction aux administrateurs (groupe ADMIN / staff) ;
- cohérence des agrégations avec des données de référence ;
- filtres de période (y compris période personnalisée et période invalide) ;
- absence totale de données personnelles dans les réponses ;
- exports CSV et Excel.
"""
from datetime import timedelta
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from courses.models import Course, Exercise, Summary, UserPersonalizedExercise
from payments.models import Abonnement, Purchase, Service
from users.models import UserProfile


def _days_ago(days, hour=12):
    return timezone.now() - timedelta(days=days, hours=12 - hour)


class StatisticsApiTests(TestCase):

    def setUp(self):
        # ── Utilisateurs ─────────────────────────────────────────────
        self.etudiant = User.objects.create_user(
            username='etudiant', email='etudiant@test.com', password='pass1234')
        UserProfile.objects.create(user=self.etudiant, groupe='ETUDIANT')

        self.admin = User.objects.create_user(
            username='admin_metier', email='admin@test.com', password='pass1234')
        UserProfile.objects.create(user=self.admin, groupe='ADMIN')

        self.staff = User.objects.create_user(
            username='admin_django', email='staff@test.com', password='pass1234',
            is_staff=True)

        # Inscriptions : l'étudiant s'est inscrit il y a 40 jours.
        User.objects.filter(pk=self.etudiant.pk).update(date_joined=_days_ago(40))
        # Les administrateurs sont "nouveaux" (inscrits aujourd'hui).

        # ── Résumés et QCM ───────────────────────────────────────────
        self.course = Course.objects.create(
            nom='Algorithmique', filiere='Informatique', university='UNIKIN')
        self.summary_old = Summary.objects.create(
            titre='Résumé ancien', texte_resume='x', course=self.course)
        self.summary_new = Summary.objects.create(
            titre='Résumé récent', texte_resume='x', course=self.course)
        Summary.objects.filter(pk=self.summary_old.pk).update(created_at=_days_ago(10))
        Summary.objects.filter(pk=self.summary_new.pk).update(created_at=_days_ago(2))

        self.exercise = Exercise.objects.create(
            summary=self.summary_old, created_by=self.admin,
            titre='QCM classique', status='completed')
        Exercise.objects.filter(pk=self.exercise.pk).update(created_at=_days_ago(3))

        self.personalized = UserPersonalizedExercise.objects.create(
            user=self.etudiant, summary=self.summary_new, seed=42,
            status='completed')
        UserPersonalizedExercise.objects.filter(pk=self.personalized.pk).update(
            created_at=_days_ago(1))

        # ── Paiements ────────────────────────────────────────────────
        self.service = Service.objects.create(
            nom='Premium', description='Accès premium', type='premium',
            price=5000, currency='CDF', duree_mois=1)

        self.purchase_completed = Purchase.objects.create(
            user=self.etudiant, summary=self.summary_old, amount=1000,
            payment_method='mobile_money', status='completed',
            completed_at=timezone.now())
        Purchase.objects.filter(pk=self.purchase_completed.pk).update(
            created_at=_days_ago(2))

        self.purchase_pending = Purchase.objects.create(
            user=self.etudiant, summary=self.summary_new, amount=1000,
            payment_method='mobile_money', status='pending')
        Purchase.objects.filter(pk=self.purchase_pending.pk).update(
            created_at=_days_ago(1))

        self.purchase_failed = Purchase.objects.create(
            user=self.etudiant, summary=self.summary_old, amount=1000,
            payment_method='mobile_money', status='failed')
        Purchase.objects.filter(pk=self.purchase_failed.pk).update(
            created_at=_days_ago(25))

        self.subscription_purchase = Purchase.objects.create(
            user=self.etudiant, service=self.service, amount=5000,
            payment_method='mobile_money', status='completed',
            completed_at=timezone.now())
        Purchase.objects.filter(pk=self.subscription_purchase.pk).update(
            created_at=_days_ago(5))

        self.refunded_purchase = Purchase.objects.create(
            user=self.etudiant, service=self.service, amount=5000,
            payment_method='mobile_money', status='refunded')
        Purchase.objects.filter(pk=self.refunded_purchase.pk).update(
            created_at=_days_ago(20))

        # ── Abonnements ──────────────────────────────────────────────
        self.abonnement_active = Abonnement.objects.create(
            user=self.etudiant, service=self.service,
            date_fin=timezone.now() + timedelta(days=25), status='active')
        Abonnement.objects.filter(pk=self.abonnement_active.pk).update(
            created_at=_days_ago(5))

        self.abonnement_expired = Abonnement.objects.create(
            user=self.etudiant, service=self.service,
            date_fin=_days_ago(3), status='expired')
        Abonnement.objects.filter(pk=self.abonnement_expired.pk).update(
            created_at=_days_ago(30))

        self.abonnement_cancelled = Abonnement.objects.create(
            user=self.etudiant, service=self.service,
            date_fin=timezone.now() + timedelta(days=10), status='cancelled')
        Abonnement.objects.filter(pk=self.abonnement_cancelled.pk).update(
            created_at=_days_ago(15))

        # ── Client API ───────────────────────────────────────────────
        self.client = APIClient()

    # ══════════════════════════════════════════════════════════════
    # Permissions
    # ══════════════════════════════════════════════════════════════

    def test_non_admin_forbidden(self):
        self.client.force_authenticate(self.etudiant)
        for url in ('admin-statistics-overview', 'admin-statistics-users',
                    'admin-statistics-summaries', 'admin-statistics-qcm',
                    'admin-statistics-transactions', 'admin-statistics-purchases',
                    'admin-statistics-subscriptions', 'admin-statistics-revenue',
                    'admin-statistics-export-csv', 'admin-statistics-export-excel'):
            response = self.client.get(reverse(url))
            self.assertEqual(response.status_code, 403, f'{url} accessible au non-admin')

    def test_anonymous_forbidden(self):
        response = self.client.get(reverse('admin-statistics-overview'))
        self.assertEqual(response.status_code, 401)

    def test_admin_group_allowed(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('admin-statistics-overview'))
        self.assertEqual(response.status_code, 200)

    def test_staff_allowed(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(reverse('admin-statistics-overview'))
        self.assertEqual(response.status_code, 200)

    # ══════════════════════════════════════════════════════════════
    # Agrégations (période par défaut : 30 derniers jours)
    # ══════════════════════════════════════════════════════════════

    def test_overview(self):
        self.client.force_authenticate(self.admin)
        data = self.client.get(reverse('admin-statistics-overview')).json()['data']
        self.assertEqual(data['users']['total'], 3)
        self.assertEqual(data['users']['new_in_period'], 2)
        self.assertEqual(data['summaries']['total'], 2)
        self.assertEqual(data['summaries']['in_period'], 2)
        self.assertEqual(data['qcm']['total'], 2)
        self.assertEqual(data['qcm']['in_period'], 2)
        self.assertEqual(data['transactions']['total'], 5)
        self.assertEqual(data['transactions']['succeeded'], 2)  # 2 completed dans la période
        self.assertEqual(data['purchases']['total'], 1)  # 1 achat de résumé réussi
        self.assertEqual(data['subscriptions']['active'], 1)
        self.assertEqual(data['revenue']['total'], 6000.0)  # 1000 + 5000
        self.assertEqual(data['revenue']['in_period'], 6000.0)

    def test_users(self):
        self.client.force_authenticate(self.admin)
        data = self.client.get(reverse('admin-statistics-users')).json()['data']
        self.assertEqual(data['total'], 3)
        self.assertEqual(data['new_in_period'], 2)
        self.assertEqual(data['daily'][-1]['date'], timezone.localtime(timezone.now()).strftime('%Y-%m-%d'))
        self.assertEqual(data['daily'][-1]['count'], 2)

    def test_summaries(self):
        self.client.force_authenticate(self.admin)
        data = self.client.get(reverse('admin-statistics-summaries')).json()['data']
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['in_period'], 2)

    def test_qcm(self):
        self.client.force_authenticate(self.admin)
        data = self.client.get(reverse('admin-statistics-qcm')).json()['data']
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['classic_total'], 1)
        self.assertEqual(data['personalized_total'], 1)
        self.assertEqual(data['in_period'], 2)

    def test_transactions(self):
        self.client.force_authenticate(self.admin)
        data = self.client.get(reverse('admin-statistics-transactions')).json()['data']
        self.assertEqual(data['total'], 5)
        self.assertEqual(data['by_status']['pending'], 1)
        self.assertEqual(data['by_status']['completed'], 2)
        self.assertEqual(data['by_status']['failed'], 1)
        self.assertEqual(data['by_status']['refunded'], 1)  # 1 refunded dans la fenêtre
        self.assertEqual(data['success_rate'], 40.0)  # 2 réussies / 5
        # Filtre par statut
        response = self.client.get(reverse('admin-statistics-transactions'),
                                   {'status': 'completed'})
        self.assertEqual(response.json()['data']['total'], 2)

    def test_purchases(self):
        self.client.force_authenticate(self.admin)
        data = self.client.get(reverse('admin-statistics-purchases')).json()['data']
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['in_period'], 1)
        self.assertEqual(data['amount_total'], 1000.0)
        self.assertEqual(data['amount_in_period'], 1000.0)
        self.assertEqual(data['avg_basket'], 1000.0)

    def test_subscriptions(self):
        self.client.force_authenticate(self.admin)
        data = self.client.get(reverse('admin-statistics-subscriptions')).json()['data']
        self.assertEqual(data['active'], 1)
        # 2 abonnements créés dans la fenêtre : actif (5 j) + annulé (15 j).
        self.assertEqual(data['new_in_period'], 2)
        self.assertIsNone(data['renewed'])
        self.assertTrue(data['renewed_not_trackable'])
        self.assertEqual(data['expired'], 1)
        self.assertEqual(data['cancelled'], 1)
        self.assertEqual(data['revenue']['amount_total'], 5000.0)
        self.assertEqual(data['revenue']['amount_in_period'], 5000.0)

    def test_revenue(self):
        self.client.force_authenticate(self.admin)
        data = self.client.get(reverse('admin-statistics-revenue')).json()['data']
        self.assertEqual(data['purchases']['quantity'], 1)
        self.assertEqual(data['purchases']['amount_total'], 1000.0)
        self.assertEqual(data['subscriptions']['quantity'], 1)
        self.assertEqual(data['subscriptions']['amount_total'], 5000.0)
        self.assertEqual(data['total']['amount_total'], 6000.0)
        self.assertEqual(data['total']['amount_in_period'], 6000.0)
        # Période précédente : aucun paiement avant la fenêtre → évolution None.
        self.assertIsNone(data['evolution_percent'])

    # ══════════════════════════════════════════════════════════════
    # Périodes
    # ══════════════════════════════════════════════════════════════

    def test_period_filters(self):
        self.client.force_authenticate(self.admin)
        for period in ('today', 'last_7_days', 'last_30_days', 'this_week',
                       'this_month', 'last_month'):
            response = self.client.get(reverse('admin-statistics-summaries'),
                                       {'period': period})
            self.assertEqual(response.status_code, 200, f'période {period} refusée')
            self.assertEqual(response.json()['period']['key'], period)

    def test_custom_period(self):
        self.client.force_authenticate(self.admin)
        start = (timezone.now() - timedelta(days=6)).strftime('%Y-%m-%d')
        end = (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(reverse('admin-statistics-summaries'),
                                   {'period': 'custom', 'start_date': start, 'end_date': end})
        self.assertEqual(response.status_code, 200)
        # Seul le résumé créé il y a 2 jours tombe dans cette fenêtre.
        self.assertEqual(response.json()['data']['in_period'], 1)

    def test_invalid_period(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('admin-statistics-summaries'),
                                   {'period': 'inconnu'})
        self.assertEqual(response.status_code, 400)

    # ══════════════════════════════════════════════════════════════
    # Page du dashboard administrateur
    # ══════════════════════════════════════════════════════════════

    def test_dashboard_page_served(self):
        response = self.client.get('/admin-dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Statistiques')
        self.assertContains(response, 'admin_dashboard/app.js')

    # ══════════════════════════════════════════════════════════════
    # Anonymisation : aucune donnée personnelle dans les réponses
    # ══════════════════════════════════════════════════════════════

    def test_no_personal_data_in_responses(self):
        self.client.force_authenticate(self.admin)
        urls = ('admin-statistics-overview', 'admin-statistics-users',
                'admin-statistics-summaries', 'admin-statistics-qcm',
                'admin-statistics-transactions', 'admin-statistics-purchases',
                'admin-statistics-subscriptions', 'admin-statistics-revenue')
        for url in urls:
            payload = json.dumps(self.client.get(reverse(url)).json())
            for secret in ('etudiant@test.com', 'admin@test.com', 'staff@test.com',
                           'etudiant', 'admin_metier', 'admin_django',
                           '+243', 'token', 'password'):
                self.assertNotIn(secret, payload, f'donnée personnelle dans {url}')

    # ══════════════════════════════════════════════════════════════
    # Exports
    # ══════════════════════════════════════════════════════════════

    def test_export_csv(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('admin-statistics-export-csv'),
                                   {'section': 'overview'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn('Utilisateurs (total)', response.content.decode('utf-8'))

    def test_export_csv_invalid_section(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('admin-statistics-export-csv'),
                                   {'section': 'nimporte'})
        self.assertEqual(response.status_code, 400)

    def test_export_excel(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('admin-statistics-export-excel'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])
        self.assertGreater(len(response.content), 1000)

    def test_export_respects_period(self):
        self.client.force_authenticate(self.admin)
        start = (timezone.now() - timedelta(days=6)).strftime('%Y-%m-%d')
        end = (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(reverse('admin-statistics-export-csv'),
                                   {'section': 'summaries', 'period': 'custom',
                                    'start_date': start, 'end_date': end})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Période personnalisée', response.content.decode('utf-8'))
