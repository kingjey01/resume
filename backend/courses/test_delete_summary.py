"""
Tests de la suppression d'un résumé EN ATTENTE de validation.

Règle métier : un CP / Admin peut supprimer un résumé qui n'est pas encore
validé. Un résumé validé (publié) reste protégé, tout comme un résumé lié à
un achat, afin de ne jamais détruire de trace financière ni de référence
orpheline.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from payments.models import Purchase

from .models import Course, Exercise, Summary, Universite, Filiere, Promotion
from users.models import UserProfile


class DeletePendingSummaryTest(TestCase):
    def setUp(self):
        self.universite = Universite.objects.create(nom='U')
        self.filiere = Filiere.objects.create(nom='Info')
        self.promotion = Promotion.objects.create(nom='P1')

        self.course = Course.objects.create(nom='Cours', filiere='Info', university='U')

        self.cp_user = self._creer_user('cp_user', 'CP')
        self.etudiant = self._creer_user('etudiant', 'ETUDIANT')

        self.client = APIClient()

    def _creer_user(self, username, groupe):
        user = User.objects.create_user(username=username, password='x')
        UserProfile.objects.create(
            user=user,
            groupe=groupe,
            universite=self.universite,
            filiere=self.filiere,
            promotion=self.promotion,
        )
        return user

    def _creer_resume(self, **kwargs):
        params = {
            'titre': 'Résumé',
            'texte_resume': 'contenu du résumé',
            'course': self.course,
            'author_type': 'ai',
            'author_user': self.cp_user,
            'prix': 500,
            'is_validated': False,
        }
        params.update(kwargs)
        return Summary.objects.create(**params)

    def _url(self, summary):
        return reverse('delete-summary', args=[summary.id])

    def test_cp_supprime_un_resume_en_attente(self):
        summary = self._creer_resume()
        self.client.force_authenticate(user=self.cp_user)

        response = self.client.delete(self._url(summary))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Summary.objects.filter(id=summary.id).exists())

    def test_suppression_nettoie_les_exercices_lies(self):
        summary = self._creer_resume()
        Exercise.objects.create(
            summary=summary,
            created_by=self.cp_user,
            titre='Exercice',
            status='completed',
        )
        self.client.force_authenticate(user=self.cp_user)

        response = self.client.delete(self._url(summary))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted_exercises'], 1)
        self.assertEqual(Exercise.objects.filter(summary_id=summary.id).count(), 0)

    def test_refus_si_le_resume_est_valide(self):
        summary = self._creer_resume(is_validated=True)
        self.client.force_authenticate(user=self.cp_user)

        response = self.client.delete(self._url(summary))

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Summary.objects.filter(id=summary.id).exists())

    def test_refus_si_le_resume_est_lie_a_un_achat(self):
        summary = self._creer_resume()
        Purchase.objects.create(
            user=self.etudiant,
            summary=summary,
            amount=500,
            payment_method='mobile_money',
            status='completed',
        )
        self.client.force_authenticate(user=self.cp_user)

        response = self.client.delete(self._url(summary))

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Summary.objects.filter(id=summary.id).exists())
        self.assertTrue(Purchase.objects.filter(summary=summary).exists())

    def test_refus_pour_un_etudiant(self):
        summary = self._creer_resume()
        self.client.force_authenticate(user=self.etudiant)

        response = self.client.delete(self._url(summary))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Summary.objects.filter(id=summary.id).exists())

    def test_refus_si_non_authentifie(self):
        summary = self._creer_resume()
        self.client.force_authenticate(user=None)

        response = self.client.delete(self._url(summary))

        self.assertIn(response.status_code, (401, 403))
        self.assertTrue(Summary.objects.filter(id=summary.id).exists())

    def test_404_si_le_resume_nexiste_pas(self):
        self.client.force_authenticate(user=self.cp_user)

        response = self.client.delete(reverse('delete-summary', args=[999999]))

        self.assertEqual(response.status_code, 404)
