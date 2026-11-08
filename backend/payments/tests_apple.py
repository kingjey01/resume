"""Tests Apple In-App Purchase (tâche 71).

Aucun appel Apple réel : le vérificateur est remplacé par un faux objet.

    PYTHONIOENCODING=utf-8 python manage.py test payments.tests_apple \
      --settings=resume_backend.settings_test
"""

import json
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from courses.models import Course, Summary, Universite, Filiere, Promotion
from users.models import UserProfile

from .models import Abonnement, AppleNotification, AppleTransaction, Purchase, Service

BUNDLE_ID = 'com.kingjey01.resumeplus'
SUMMARY_PRODUCT = 'com.kingjey01.resumeplus.summary.1000'
SUB_PRODUCT = 'com.kingjey01.resumeplus.qcm.monthly'


def _payload(
    *, product_id=SUMMARY_PRODUCT, transaction_id='tx-1',
    original_id='orig-1', expires_ms=None, purchase_ms=1_700_000_000_000,
    revocation_ms=None, app_account_token=None,
):
    return SimpleNamespace(
        bundleId=BUNDLE_ID,
        productId=product_id,
        transactionId=transaction_id,
        originalTransactionId=original_id,
        purchaseDate=purchase_ms,
        expiresDate=expires_ms,
        environment='Sandbox',
        revocationDate=revocation_ms,
        revocationReason=None,
        appAccountToken=app_account_token,
    )


class FakeVerifier:
    def __init__(self, payload=None, notification=None):
        self.payload = payload
        self.notification = notification

    def verify_and_decode_signed_transaction(self, signed):
        if signed == 'bad':
            from appstoreserverlibrary.signed_data_verifier import VerificationException
            raise VerificationException(1, 'invalid')
        if self.payload is None:
            raise ValueError('no payload')
        return self.payload

    def verify_and_decode_notification(self, signed):
        return self.notification


@override_settings(
    APPLE_BUNDLE_ID=BUNDLE_ID,
    APPLE_ENVIRONMENT='Sandbox',
    APPLE_SUMMARY_PRODUCTS=json.dumps({SUMMARY_PRODUCT: 1000}),
    DEBUG=True,
    ENABLE_CATALOG_CACHE=False,
)
class AppleIapTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.universite = Universite.objects.create(nom='Université IAP')
        cls.filiere = Filiere.objects.create(nom='Filière IAP')
        cls.promotion = Promotion.objects.create(nom='Promo IAP', annee=2026)

        cls.user = User.objects.create_user(
            username='iap_user', password='testpass123',
            first_name='Iap', last_name='User',
        )
        UserProfile.objects.create(
            user=cls.user, groupe='ETUDIANT',
            universite=cls.universite, filiere=cls.filiere,
            promotion=cls.promotion,
        )
        cls.other = User.objects.create_user(
            username='iap_other', password='testpass123',
        )
        UserProfile.objects.create(user=cls.other, groupe='ETUDIANT')

        cls.course = Course.objects.create(
            nom='Cours IAP', filiere='Filière IAP', university='Université IAP',
        )
        cls.course.universites.add(cls.universite)
        cls.course.filieres.add(cls.filiere)
        cls.course.promotions.add(cls.promotion)

        cls.summary = Summary.objects.create(
            titre='Résumé IAP', texte_resume='Contenu',
            course=cls.course, author_type='cp',
            is_validated=True, prix=1000,
        )
        cls.service = Service.objects.create(
            nom='QCM IAP', description='QCM', type='basic',
            price=5000, currency='CDF', duree_mois=1,
            apple_product_id=SUB_PRODUCT,
        )

    def _client(self, user=None):
        client = APIClient()
        token = str(RefreshToken.for_user(user or self.user).access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client

    def _verify_summary(self, *, transaction_id='tx-summary', payload=None):
        payload = payload or _payload(transaction_id=transaction_id)
        with patch('payments.apple_iap.get_verifier',
                   return_value=FakeVerifier(payload=payload)):
            return self._client().post(
                '/api/apple/verify/',
                {
                    'signed_transaction': 'signed',
                    'summary_id': self.summary.id,
                },
            )

    # ── Configuration produits ────────────────────────────────────────────

    def test_produits_apple_publics(self):
        response = self._client().get('/api/apple/products/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['summary_products'][0]['product_id'], SUMMARY_PRODUCT)
        self.assertEqual(data['subscriptions'][0]['product_id'], SUB_PRODUCT)
        self.assertNotIn('apiKey', data)

    def test_endpoint_verification_authentifie(self):
        response = APIClient().post('/api/apple/verify/', {'signed_transaction': 'x'})
        self.assertEqual(response.status_code, 401)

    # ── Achat de résumé ───────────────────────────────────────────────────

    def test_achat_resume_apple_et_idempotence(self):
        first = self._verify_summary()
        self.assertEqual(first.status_code, 200, first.content)

        purchase = Purchase.objects.get(user=self.user, summary=self.summary)
        self.assertEqual(purchase.source, 'apple')
        self.assertEqual(purchase.payment_method, 'apple')
        self.assertEqual(purchase.status, 'completed')
        self.assertEqual(purchase.apple_transaction_id, 'tx-summary')
        self.assertEqual(AppleTransaction.objects.count(), 1)

        second = self._verify_summary()
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Purchase.objects.filter(summary=self.summary).count(), 1)
        self.assertEqual(AppleTransaction.objects.count(), 1)

    def test_transaction_deja_utilisee_par_un_autre_compte(self):
        self.assertEqual(self._verify_summary().status_code, 200)

        payload = _payload(transaction_id='tx-summary')
        with patch('payments.apple_iap.get_verifier',
                   return_value=FakeVerifier(payload=payload)):
            response = self._client(self.other).post(
                '/api/apple/verify/',
                {
                    'signed_transaction': 'signed',
                    'summary_id': self.summary.id,
                },
            )
        self.assertEqual(response.status_code, 409)
        self.assertFalse(
            Purchase.objects.filter(user=self.other, summary=self.summary).exists()
        )

    def test_prix_produit_incoherent_refuse(self):
        self.summary.prix = 500
        self.summary.save(update_fields=['prix'])
        response = self._verify_summary()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Purchase.objects.exists())

    def test_produit_inconnu_refuse(self):
        payload = _payload(product_id='produit.inconnu')
        with patch('payments.apple_iap.get_verifier',
                   return_value=FakeVerifier(payload=payload)):
            response = self._client().post(
                '/api/apple/verify/',
                {'signed_transaction': 'signed', 'summary_id': self.summary.id},
            )
        self.assertEqual(response.status_code, 400)

    def test_bundle_id_incoherent_refuse(self):
        payload = _payload()
        payload.bundleId = 'com.autre.bundle'
        response = self._verify_summary(payload=payload)
        self.assertEqual(response.status_code, 400)

    def test_signature_invalide_refusee(self):
        with patch('payments.apple_iap.get_verifier',
                   return_value=FakeVerifier(payload=_payload())):
            response = self._client().post(
                '/api/apple/verify/',
                {'signed_transaction': 'bad', 'summary_id': self.summary.id},
            )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Purchase.objects.exists())

    # ── Abonnement ────────────────────────────────────────────────────────

    def test_abonnement_apple_cree(self):
        expires = 1_900_000_000_000
        payload = _payload(
            product_id=SUB_PRODUCT, transaction_id='tx-sub',
            original_id='orig-sub', expires_ms=expires,
        )
        with patch('payments.apple_iap.get_verifier',
                   return_value=FakeVerifier(payload=payload)):
            response = self._client().post(
                '/api/apple/verify/', {'signed_transaction': 'signed'},
            )
        self.assertEqual(response.status_code, 200, response.content)

        abonnement = Abonnement.objects.get(user=self.user, service=self.service)
        self.assertEqual(abonnement.source, 'apple')
        self.assertEqual(abonnement.status, 'active')
        self.assertEqual(
            abonnement.apple_original_transaction_id, 'orig-sub'
        )
        self.assertTrue(abonnement.auto_renew)
        self.assertEqual(Purchase.objects.get(service=self.service).source, 'apple')

    # ── Notifications ─────────────────────────────────────────────────────

    def _notification(self, notification_type, *, payload, uuid='notif-1',
                      subtype=None):
        notification = SimpleNamespace(
            notificationUUID=uuid,
            notificationType=notification_type,
            subtype=subtype,
            data=SimpleNamespace(
                signedTransactionInfo='signed',
                transactionId=getattr(payload, 'transactionId', None),
                environment='Sandbox',
            ),
        )
        return patch('payments.apple_iap.get_verifier',
                     return_value=FakeVerifier(
                         payload=payload, notification=notification
                     ))

    def _post_notification(self):
        return self.client.post(
            '/api/apple/notifications/',
            data=json.dumps({'signedPayload': 'signed'}),
            content_type='application/json',
        )

    def _verify_subscription(self, payload):
        with patch('payments.apple_iap.get_verifier',
                   return_value=FakeVerifier(payload=payload)):
            return self._client().post(
                '/api/apple/verify/', {'signed_transaction': 'signed'},
            )

    def test_notification_apres_validation_client_et_doublon(self):
        expires = 1_900_000_000_000
        payload = _payload(
            product_id=SUB_PRODUCT, transaction_id='tx-notif',
            original_id='orig-notif', expires_ms=expires,
        )
        # Le client valide la transaction avant que la notification n'arrive :
        # c'est ce qui rattache la transaction au compte Django.
        self.assertEqual(self._verify_subscription(payload).status_code, 200)

        with self._notification('SUBSCRIBED', payload=payload, uuid='n-sub'):
            first = self._post_notification()
        self.assertEqual(first.status_code, 200, first.content)

        self.assertTrue(
            Abonnement.objects.filter(
                user=self.user, service=self.service, source='apple'
            ).exists()
        )
        self.assertEqual(AppleTransaction.objects.count(), 1)
        self.assertEqual(Abonnement.objects.filter(service=self.service).count(), 1)

        # Même notification rejouée : aucun double traitement.
        with self._notification('SUBSCRIBED', payload=payload, uuid='n-sub'):
            second = self._post_notification()
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()['status'], 'duplicate')
        self.assertEqual(Abonnement.objects.filter(service=self.service).count(), 1)
        self.assertEqual(AppleNotification.objects.count(), 1)

    def test_notification_initiale_avec_app_account_token(self):
        from .apple_iap import app_account_token_for_user

        token = str(app_account_token_for_user(self.user.id))
        profile = self.user.profile
        profile.apple_app_account_token = token
        profile.save(update_fields=['apple_app_account_token'])

        expires = 1_900_000_000_000
        payload = _payload(
            product_id=SUB_PRODUCT, transaction_id='tx-token',
            original_id='orig-token', expires_ms=expires,
            app_account_token=token,
        )

        with self._notification('SUBSCRIBED', payload=payload, uuid='n-token'):
            response = self._post_notification()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['status'], 'processed')

        self.assertTrue(
            Abonnement.objects.filter(
                user=self.user, service=self.service, source='apple'
            ).exists()
        )

    def test_notification_renouvellement_prolonge_abonnement(self):
        expires_initial = 1_900_000_000_000
        initial = _payload(
            product_id=SUB_PRODUCT, transaction_id='tx-renew-1',
            original_id='orig-renew', expires_ms=expires_initial,
        )
        self.assertEqual(self._verify_subscription(initial).status_code, 200)

        abonnement = Abonnement.objects.get(service=self.service)
        date_fin_initiale = abonnement.date_fin

        expires_renouvellement = expires_initial + 30 * 24 * 3600 * 1000
        renewal = _payload(
            product_id=SUB_PRODUCT, transaction_id='tx-renew-2',
            original_id='orig-renew', expires_ms=expires_renouvellement,
        )
        with self._notification('DID_RENEW', payload=renewal, uuid='n-renew'):
            response = self._post_notification()
        self.assertEqual(response.status_code, 200, response.content)

        abonnement.refresh_from_db()
        self.assertGreater(abonnement.date_fin, date_fin_initiale)
        self.assertEqual(AppleTransaction.objects.count(), 2)

    def test_notification_expiration(self):
        expires = 1_900_000_000_000
        payload = _payload(
            product_id=SUB_PRODUCT, transaction_id='tx-exp',
            original_id='orig-exp', expires_ms=expires,
        )
        self.assertEqual(self._verify_subscription(payload).status_code, 200)

        with self._notification('EXPIRED', payload=payload, uuid='n-exp'):
            response = self._post_notification()
        self.assertEqual(response.status_code, 200)
        abonnement = Abonnement.objects.get(service=self.service)
        self.assertEqual(abonnement.status, 'expired')

    def test_notification_remboursement_resume(self):
        self.assertEqual(self._verify_summary().status_code, 200)
        purchase = Purchase.objects.get(summary=self.summary)

        payload = _payload(transaction_id='tx-summary')
        with self._notification('REFUND', payload=payload, uuid='n-refund'):
            response = self._post_notification()
        self.assertEqual(response.status_code, 200)

        purchase.refresh_from_db()
        self.assertEqual(purchase.status, 'refunded')
