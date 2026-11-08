"""Tests du seed de déploiement (tâche 71 / déploiement)."""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from courses.models import Filiere, Promotion, Universite
from payments.models import Service


class SeedDeploymentTest(TestCase):
    def _run(self, **options):
        out = StringIO()
        call_command('seed_deployment', stdout=out, **options)
        return out.getvalue()

    def test_cree_referentiels_et_service_qcm_sans_utilisateur(self):
        self._run(
            qcm_product_id='com.test.qcm.monthly',
            summary_products=['com.test.summary.300=300'],
        )

        qcm = Service.objects.get(nom='Abonnement QCM')
        self.assertEqual(qcm.apple_product_id, 'com.test.qcm.monthly')
        self.assertEqual(qcm.currency, 'CDF')
        self.assertTrue(qcm.is_active)

        self.assertTrue(Universite.objects.filter(nom='Université de Kinshasa').exists())
        self.assertEqual(Filiere.objects.count(), 6)
        self.assertEqual(Promotion.objects.count(), 5)

    def test_idempotent(self):
        self._run(qcm_product_id='com.test.qcm.monthly')
        self._run(qcm_product_id='com.test.qcm.monthly')

        self.assertEqual(Service.objects.filter(nom='Abonnement QCM').count(), 1)
        self.assertEqual(Universite.objects.count(), 1)
        self.assertEqual(Filiere.objects.count(), 6)
        self.assertEqual(Promotion.objects.count(), 5)

    def test_dry_run_n_ecrit_rien(self):
        self._run(dry_run=True, qcm_product_id='com.test.qcm.monthly')

        self.assertFalse(Service.objects.exists())
        self.assertFalse(Universite.objects.exists())

    def test_update_existing_optionnel(self):
        Service.objects.create(
            nom='Abonnement QCM',
            description='Ancien',
            type='basic',
            price=1000,
            currency='CDF',
            duree_mois=1,
            features=[],
        )

        self._run(qcm_product_id='com.test.qcm.monthly')
        service = Service.objects.get(nom='Abonnement QCM')
        self.assertEqual(service.apple_product_id, '')
        self.assertEqual(service.price, 1000)

        self._run(
            update_existing=True,
            qcm_product_id='com.test.qcm.monthly',
            qcm_price='5000',
        )
        service.refresh_from_db()
        self.assertEqual(service.apple_product_id, 'com.test.qcm.monthly')
        self.assertEqual(service.price, 5000)
