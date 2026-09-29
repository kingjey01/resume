"""
Tests de la règle métier : un résumé DÉJÀ ACHETÉ est intouchable.

La règle est double — « invalidé ou supprimé un résumé déjà acheté doit être
impossible ». Elle complète `test_delete_summary.py`, qui couvre la suppression
via l'endpoint dédié, sur les deux points qui n'étaient pas protégés :

1. l'INVALIDATION (`POST /summaries/<id>/validate/` avec `is_validated=false`),
   qui ne contrôlait rien ;
2. les écritures génériques de `SummaryDetailView` (`PATCH` / `DELETE` sur
   `/summaries/<pk>/`), qui offraient un contournement direct aux règles des
   endpoints dédiés — y compris à la règle de suppression qui existait déjà.

Chaque test de refus est doublé d'un test de NON-RÉGRESSION sur le cas autorisé,
pour prouver que le contrôle ne bloque que l'opération interdite.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from payments.models import Purchase

from .models import Course, Filiere, Promotion, Summary, Universite
from users.models import UserProfile


class ResumeAcheteIntouchableTest(TestCase):
    def setUp(self):
        self.universite = Universite.objects.create(nom='U')
        self.filiere = Filiere.objects.create(nom='Info')
        self.promotion = Promotion.objects.create(nom='P1')

        self.course = Course.objects.create(nom='Cours', filiere='Info', university='U')
        # Nécessaires pour que `HasUniversityAccess` (vue détail) laisse passer.
        self.course.universites.add(self.universite)
        self.course.filieres.add(self.filiere)
        self.course.promotions.add(self.promotion)

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

    def _acheter(self, summary, statut='completed'):
        return Purchase.objects.create(
            user=self.etudiant,
            summary=summary,
            amount=500,
            payment_method='mobile_money',
            status=statut,
        )

    # ───────────────────────── Invalidation (endpoint dédié) ─────────────────

    def test_invalidation_refusee_si_le_resume_est_achete(self):
        summary = self._creer_resume(is_validated=True)
        self._acheter(summary)
        self.client.force_authenticate(user=self.cp_user)

        response = self.client.post(
            reverse('validate-summary', args=[summary.id]),
            {'is_validated': False},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        summary.refresh_from_db()
        self.assertTrue(summary.is_validated)  # toujours publié
        self.assertIn('acheté', str(response.data['error']))

    def test_invalidation_ok_si_aucun_achat(self):
        """Non-régression : invalider reste possible sans achat."""
        summary = self._creer_resume(is_validated=True)
        self.client.force_authenticate(user=self.cp_user)

        response = self.client.post(
            reverse('validate-summary', args=[summary.id]),
            {'is_validated': False},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        summary.refresh_from_db()
        self.assertFalse(summary.is_validated)

    def test_invalidation_refusee_des_le_premier_achat_quel_que_soit_le_statut(self):
        """Même critère que la suppression : toute trace d'achat protège."""
        for statut in ('completed', 'pending', 'failed', 'refunded'):
            with self.subTest(statut=statut):
                summary = self._creer_resume(is_validated=True, titre=f'R {statut}')
                self._acheter(summary, statut=statut)
                self.client.force_authenticate(user=self.cp_user)

                response = self.client.post(
                    reverse('validate-summary', args=[summary.id]),
                    {'is_validated': False},
                    format='json',
                )

                self.assertEqual(response.status_code, 400)
                summary.refresh_from_db()
                self.assertTrue(summary.is_validated)

    def test_revalidation_ok_si_le_resume_est_achete(self):
        """Non-régression : re-publier un résumé acheté reste possible."""
        summary = self._creer_resume(is_validated=False)
        self._acheter(summary)
        self.client.force_authenticate(user=self.cp_user)

        response = self.client.post(
            reverse('validate-summary', args=[summary.id]),
            {'is_validated': True},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        summary.refresh_from_db()
        self.assertTrue(summary.is_validated)

    def test_invalidation_refusee_pour_un_etudiant(self):
        """Non-régression : la permission CP/Admin est inchangée."""
        summary = self._creer_resume(is_validated=True)
        self.client.force_authenticate(user=self.etudiant)

        response = self.client.post(
            reverse('validate-summary', args=[summary.id]),
            {'is_validated': False},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        summary.refresh_from_db()
        self.assertTrue(summary.is_validated)

    # ───────────────────────── Liste de validation ───────────────────────────

    def test_liste_validation_expose_has_purchases(self):
        """Le CP doit pouvoir savoir qu'une action sera refusée."""
        achete = self._creer_resume(is_validated=True, titre='Acheté')
        self._acheter(achete)
        self._creer_resume(is_validated=True, titre='Non acheté')
        self.client.force_authenticate(user=self.cp_user)

        response = self.client.get(reverse('summaries-validation'))

        self.assertEqual(response.status_code, 200)
        par_titre = {s['titre']: s for s in response.data['summaries']}
        self.assertTrue(par_titre['Acheté']['has_purchases'])
        self.assertFalse(par_titre['Non acheté']['has_purchases'])
        # Les champs existants de la réponse n'ont pas bougé.
        for champ in ('id', 'titre', 'is_validated', 'prix', 'is_free',
                      'course_name', 'author_type', 'author_name'):
            self.assertIn(champ, par_titre['Acheté'])

    # ───────── Écritures génériques de SummaryDetailView (contournement) ─────

    def test_patch_detail_view_refuse_l_invalidation_d_un_resume_achete(self):
        summary = self._creer_resume(is_validated=True)
        self._acheter(summary)
        self.client.force_authenticate(user=self.cp_user)

        response = self.client.patch(
            reverse('summary-detail', args=[summary.pk]),
            {'is_validated': False},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        summary.refresh_from_db()
        self.assertTrue(summary.is_validated)

    def test_patch_detail_view_invalidation_ok_si_aucun_achat(self):
        """Non-régression : PATCH reste fonctionnel sans achat."""
        summary = self._creer_resume(is_validated=True)
        self.client.force_authenticate(user=self.cp_user)

        response = self.client.patch(
            reverse('summary-detail', args=[summary.pk]),
            {'is_validated': False},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        summary.refresh_from_db()
        self.assertFalse(summary.is_validated)

    def test_delete_detail_view_refuse_si_le_resume_est_achete(self):
        """La trace financière ne doit pas disparaître en cascade."""
        summary = self._creer_resume(is_validated=False)
        self._acheter(summary)
        self.client.force_authenticate(user=self.cp_user)

        response = self.client.delete(reverse('summary-detail', args=[summary.pk]))

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Summary.objects.filter(id=summary.id).exists())
        self.assertTrue(Purchase.objects.filter(summary_id=summary.id).exists())

    def test_delete_detail_view_refuse_si_le_resume_est_valide(self):
        """Même règle que l'endpoint dédié `delete_summary_view`."""
        summary = self._creer_resume(is_validated=True)
        self.client.force_authenticate(user=self.cp_user)

        response = self.client.delete(reverse('summary-detail', args=[summary.pk]))

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Summary.objects.filter(id=summary.id).exists())
