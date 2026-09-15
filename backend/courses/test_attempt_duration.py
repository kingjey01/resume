from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import (
    Course,
    Summary,
    UserPersonalizedExercise,
    UserPersonalizedQuestion,
)


class PersonalizedAttemptDurationTest(TestCase):
    """La durée d'une tentative personnalisée doit venir du client.

    Côté serveur la tentative est créée AU MOMENT de la soumission
    (`started_at` est en `auto_now_add`), donc `completed_at - started_at` ne
    vaut que quelques millisecondes : sans durée fournie par l'app, le temps
    enregistré — et donc affiché dans l'historique — restait à 0.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='dur', password='x')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        course = Course.objects.create(nom='C', filiere='Info', university='U')
        summary = Summary.objects.create(
            titre='S',
            texte_resume='contenu',
            course=course,
            author_type='cp',
            author_user=self.user,
        )
        self.exercise = UserPersonalizedExercise.objects.create(
            user=self.user,
            summary=summary,
            difficulty='easy',
            seed=1,
            status='completed',
        )
        for i, answer in enumerate(['A', 'B']):
            UserPersonalizedQuestion.objects.create(
                personalized_exercise=self.exercise,
                question_text=f'Q{i}',
                options={'A': '1', 'B': '2', 'C': '3', 'D': '4'},
                correct_answer=answer,
                order=i,
            )

    def _submit(self, payload):
        url = reverse('submit-personalized-exercise', args=[self.exercise.id])
        with patch(
            'courses.personalized_exercise_views.user_can_access_summary',
            return_value=True,
        ), patch(
            'courses.personalized_exercise_views.HasActiveSubscription.has_permission',
            return_value=True,
        ):
            return self.client.post(url, payload, format='json')

    def test_duree_fournie_par_le_client_est_enregistree(self):
        resp = self._submit(
            {'answers': {'0': 'A', '1': 'B'}, 'time_spent_seconds': 143}
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['time_spent_seconds'], 143)
        attempt = self.exercise.attempts.first()
        self.assertEqual(attempt.time_spent_seconds, 143)

    def test_sans_duree_le_comportement_historique_est_conserve(self):
        resp = self._submit({'answers': {'0': 'A', '1': 'B'}})
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['time_spent_seconds'], 0)

    def test_duree_negative_est_ramenee_a_zero(self):
        resp = self._submit(
            {'answers': {'0': 'A', '1': 'B'}, 'time_spent_seconds': -5}
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['time_spent_seconds'], 0)

    def test_duree_non_numerique_est_rejetee(self):
        resp = self._submit(
            {'answers': {'0': 'A', '1': 'B'}, 'time_spent_seconds': 'abc'}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self.exercise.attempts.count(), 0)

    def test_le_format_de_retour_est_inchange(self):
        """Aucun champ existant ne doit disparaître ni changer de nom."""
        resp = self._submit(
            {'answers': {'0': 'A', '1': 'B'}, 'time_spent_seconds': 42}
        )
        for key in (
            'attempt_id',
            'score',
            'correct_answers',
            'total_questions',
            'time_spent_seconds',
            'results',
            'message',
        ):
            self.assertIn(key, resp.data, f'champ manquant: {key}')
        self.assertIsInstance(resp.data['time_spent_seconds'], int)
        self.assertEqual(resp.data['score'], 100.0)
