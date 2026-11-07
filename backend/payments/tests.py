"""Tests — Tâche 70 : « Payer pour un autre étudiant ».

Exécuter avec les settings de test (tâches Celery synchrones) :

    python manage.py test payments.tests --settings=resume_backend.settings_test
"""

import json
import sys

# Les callbacks FlexPay contiennent des emojis dans leurs logs. La console
# Windows par défaut est en cp1252 et lèverait UnicodeEncodeError pendant les
# tests ; la production Linux est en UTF-8.
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from courses.models import Course, Summary, Universite, Filiere, Promotion
from notifications.models import UserNotification
from users.models import UserProfile

from .models import Abonnement, Purchase, Service


@override_settings(DEBUG=True, ENABLE_CATALOG_CACHE=False)
class PayForAnotherStudentTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.universite = Universite.objects.create(nom='Université t70')
        cls.filiere = Filiere.objects.create(nom='Filière t70')
        cls.promotion = Promotion.objects.create(nom='Promo t70', annee=2026)

        cls.payeur = User.objects.create_user(
            username='t70_payeur', password='testpass123',
            first_name='Alice', last_name='Payeur',
        )
        UserProfile.objects.create(
            user=cls.payeur, groupe='ETUDIANT',
            phone='0990000001',
            universite=cls.universite, filiere=cls.filiere,
            promotion=cls.promotion,
        )

        cls.beneficiaire = User.objects.create_user(
            username='t70_benef', password='testpass123',
            first_name='Bob', last_name='Beneficiaire',
        )
        UserProfile.objects.create(
            user=cls.beneficiaire, groupe='ETUDIANT',
            phone='0990000002',
            universite=cls.universite, filiere=cls.filiere,
            promotion=cls.promotion,
        )

        cls.inactif = User.objects.create_user(
            username='t70_inactif', password='testpass123', is_active=False,
        )
        UserProfile.objects.create(
            user=cls.inactif, groupe='ETUDIANT', phone='0990000003',
        )

        cls.cp = User.objects.create_user(
            username='t70_cp', password='testpass123',
        )
        UserProfile.objects.create(
            user=cls.cp, groupe='CP', phone='0990000004',
        )

        cls.course = Course.objects.create(
            nom='Cours t70', filiere='Filière t70',
            university='Université t70',
        )
        cls.course.universites.add(cls.universite)
        cls.course.filieres.add(cls.filiere)
        cls.course.promotions.add(cls.promotion)

        cls.summary = Summary.objects.create(
            titre='Résumé t70', texte_resume='Contenu',
            course=cls.course, author_type='cp',
            is_validated=True, prix=1000,
        )

        cls.service = Service.objects.create(
            nom='Exercices QCM t70', description='QCM',
            type='basic', price=5000, currency='CDF',
            duree_mois=1, quota_qcm_mensuel=10,
        )

    def _client(self, user):
        client = APIClient()
        token = str(RefreshToken.for_user(user).access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client

    # ── Vérification du bénéficiaire ──────────────────────────────────────

    def test_verification_beneficiaire_identifie_le_compte_sans_id(self):
        response = self._client(self.payeur).post(
            '/api/beneficiary/verify/', {'phone': '+243990000002'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['found'])
        self.assertEqual(data['display_name'], 'Bob Beneficiaire')
        self.assertNotIn('id', data)
        self.assertNotIn('user_id', data)

    def test_verification_refuse_son_propre_numero(self):
        response = self._client(self.payeur).post(
            '/api/beneficiary/verify/', {'phone': '0990000001'}
        )
        self.assertEqual(response.status_code, 400)

    def test_verification_refuse_inactif_non_etudiant_et_inconnu(self):
        client = self._client(self.payeur)
        for phone in ['0990000003', '0990000004', '0999999999', 'abc']:
            response = client.post('/api/beneficiary/verify/', {'phone': phone})
            self.assertIn(
                response.status_code, (400, 404),
                msg=f'{phone} → {response.status_code}',
            )

    # ── Achat de résumé ───────────────────────────────────────────────────

    def test_achat_resume_offert_attribue_au_beneficiaire(self):
        response = self._client(self.payeur).post(
            '/api/purchases/initiate/',
            {
                'summary_id': self.summary.id,
                'phone_number': '0990000001',
                'beneficiary_phone': '0990000002',
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()['success'])

        achat = Purchase.objects.get(summary=self.summary)
        self.assertEqual(achat.user_id, self.beneficiaire.id)
        self.assertEqual(achat.payer_id, self.payeur.id)
        self.assertEqual(achat.payer_phone, '0990000001')
        self.assertEqual(achat.beneficiary_phone, '0990000002')
        self.assertEqual(achat.status, 'completed')
        # Le payeur n'obtient AUCUN achat.
        self.assertFalse(
            Purchase.objects.filter(
                user=self.payeur, summary=self.summary
            ).exists()
        )

    def test_achat_pour_soi_inchange(self):
        response = self._client(self.payeur).post(
            '/api/purchases/initiate/',
            {'summary_id': self.summary.id, 'phone_number': '0990000001'},
        )
        self.assertEqual(response.status_code, 200, response.content)

        achat = Purchase.objects.get(summary=self.summary)
        self.assertEqual(achat.user_id, self.payeur.id)
        self.assertEqual(achat.payer_id, self.payeur.id)
        self.assertFalse(achat.est_cadeau)

    def test_achat_offert_refuse_si_beneficiaire_possede_deja(self):
        Purchase.objects.create(
            user=self.beneficiaire, payer=self.payeur,
            summary=self.summary, amount=1000,
            payment_method='mobile_money', status='completed',
            transaction_id='deja-complete',
        )
        response = self._client(self.payeur).post(
            '/api/purchases/initiate/',
            {
                'summary_id': self.summary.id,
                'phone_number': '0990000001',
                'beneficiary_phone': '0990000002',
            },
        )
        self.assertEqual(response.status_code, 400)

    # ── Abonnement QCM ────────────────────────────────────────────────────

    def test_abonnement_offert_attribue_au_beneficiaire(self):
        response = self._client(self.payeur).post(
            '/api/initiate-subscription-payment/',
            {
                'service_id': self.service.id,
                'phone_number': '0990000001',
                'beneficiary_phone': '0990000002',
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()['success'])

        achat = Purchase.objects.get(service=self.service)
        self.assertEqual(achat.user_id, self.beneficiaire.id)
        self.assertEqual(achat.payer_id, self.payeur.id)

        abonnement = Abonnement.objects.get(service=self.service)
        self.assertEqual(abonnement.user_id, self.beneficiaire.id)
        self.assertEqual(abonnement.payer_id, self.payeur.id)
        self.assertTrue(abonnement.est_cadeau)
        self.assertFalse(
            Abonnement.objects.filter(
                user=self.payeur, service=self.service
            ).exists()
        )

    def test_abonnement_offert_refuse_si_paiement_deja_en_cours(self):
        Purchase.objects.create(
            user=self.beneficiaire, payer=self.payeur,
            service=self.service, amount=5000,
            payment_method='mobile_money', status='pending',
            transaction_id='pending-gift-t70',
        )
        response = self._client(self.payeur).post(
            '/api/initiate-subscription-payment/',
            {
                'service_id': self.service.id,
                'phone_number': '0990000001',
                'beneficiary_phone': '0990000002',
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_abonnement_offert_refuse_si_beneficiaire_deja_actif(self):
        Abonnement.objects.create(
            user=self.beneficiaire, payer=self.payeur,
            service=self.service, status='active',
        )
        response = self._client(self.payeur).post(
            '/api/initiate-subscription-payment/',
            {
                'service_id': self.service.id,
                'phone_number': '0990000001',
                'beneficiary_phone': '0990000002',
            },
        )
        self.assertEqual(response.status_code, 400)

    # ── Suivi et callbacks idempotents ────────────────────────────────────

    def test_le_payeur_peut_suivre_la_transaction_offerte(self):
        achat = Purchase.objects.create(
            user=self.beneficiaire, payer=self.payeur,
            summary=self.summary, amount=1000,
            payment_method='mobile_money', status='pending',
            transaction_id='suivi-t70',
        )
        response = self._client(self.payeur).get(
            f'/api/purchases/check-status/{achat.transaction_id}/'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'pending')

        # Un utilisateur sans lien avec la transaction n'y a pas accès.
        tiers = User.objects.create_user(username='t70_tiers', password='x')
        UserProfile.objects.create(user=tiers, groupe='ETUDIANT')
        self.assertEqual(
            self._client(tiers).get(
                f'/api/purchases/check-status/{achat.transaction_id}/'
            ).status_code,
            404,
        )

    def test_callback_repete_n_attribue_qu_une_fois(self):
        achat = Purchase.objects.create(
            user=self.beneficiaire, payer=self.payeur,
            service=self.service, amount=5000,
            payment_method='mobile_money', status='pending',
            transaction_id='callback-t70',
        )

        payload = json.dumps({'code': '0', 'reference': achat.transaction_id})
        first = self.client.post(
            '/api/flexpay-callback/', data=payload,
            content_type='application/json',
        )
        second = self.client.post(
            '/api/flexpay-callback/', data=payload,
            content_type='application/json',
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

        achat.refresh_from_db()
        self.assertEqual(achat.status, 'completed')
        self.assertEqual(
            Abonnement.objects.filter(service=self.service).count(), 1
        )
        abonnement = Abonnement.objects.get(service=self.service)
        self.assertEqual(abonnement.user_id, self.beneficiaire.id)
        self.assertEqual(abonnement.payer_id, self.payeur.id)

    def test_callback_echec_n_attribue_rien(self):
        achat = Purchase.objects.create(
            user=self.beneficiaire, payer=self.payeur,
            service=self.service, amount=5000,
            payment_method='mobile_money', status='pending',
            transaction_id='callback-fail-t70',
        )
        payload = json.dumps(
            {'code': '1', 'reference': achat.transaction_id}
        )
        self.client.post(
            '/api/flexpay-callback/', data=payload,
            content_type='application/json',
        )
        achat.refresh_from_db()
        self.assertEqual(achat.status, 'failed')
        self.assertFalse(Abonnement.objects.filter(service=self.service).exists())

    # ── Notifications ─────────────────────────────────────────────────────

    def test_notification_achat_offert_au_beneficiaire_uniquement(self):
        achat = Purchase.objects.create(
            user=self.beneficiaire, payer=self.payeur,
            payer_phone='0990000001', beneficiary_phone='0990000002',
            summary=self.summary, amount=1000,
            payment_method='mobile_money', status='completed',
            transaction_id='notif-t70',
            completed_at=None,
        )
        # Le signal post_save a déjà exécuté la tâche (settings EAGER).
        # On ne regarde que les notifications de paiement : la création du
        # résumé en setUpTestData a déjà généré des notifications de contenu.
        notifs_benef = UserNotification.objects.filter(
            user=self.beneficiaire,
            notification__notification_type='payment',
        ).select_related('notification')
        self.assertTrue(notifs_benef.exists())
        self.assertIn('offert', notifs_benef.first().notification.title.lower())

        self.assertFalse(
            UserNotification.objects.filter(
                user=self.payeur,
                notification__notification_type='payment',
            ).exists()
        )

    def test_notification_abonnement_offert_au_beneficiaire_uniquement(self):
        abonnement = Abonnement.objects.create(
            user=self.beneficiaire, payer=self.payeur,
            service=self.service, status='active',
        )
        notifs_benef = UserNotification.objects.filter(
            user=self.beneficiaire,
            notification__notification_type='payment',
        ).select_related('notification')
        self.assertTrue(notifs_benef.exists())
        self.assertIn('offert', notifs_benef.first().notification.title.lower())

        self.assertFalse(
            UserNotification.objects.filter(
                user=self.payeur,
                notification__notification_type='payment',
            ).exists()
        )
        self.assertEqual(abonnement.user_id, self.beneficiaire.id)
