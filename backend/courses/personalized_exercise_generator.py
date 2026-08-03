"""
Générateur d'exercices QCM personnalisés avec niveaux de difficulté.
Chaque utilisateur reçoit des questions uniques pour chaque résumé.
"""
import json
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from .models import Summary, UserPersonalizedExercise
from .deepseek_service import deepseek_service

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
#  TEMPLATES DE PROMPTS PAR DIFFICULTÉ
# ═══════════════════════════════════════════════════════════════════════════════

PROMPT_TEMPLATES = {
    'easy': """
Tu es un professeur expert en pédagogie. Génère exactement 8 questions QCM FACILES (niveau débutant) 
sur le texte suivant.

INSTRUCTIONS SPÉCIFIQUES NIVEAU FACILE:
- Questions factuelles directes (qui, quoi, où, quand)
- Définitions simples trouvables directement dans le texte
- Aucun raisonnement complexe requis
- Réponses évidentes pour quelqu'un ayant lu le texte
- Questions de mémorisation basique

FORMAT JSON STRICT REQUIS:
[
  {
    "question_text": "Question claire et factuelle ?",
    "options": {
      "A": "Option A (distractor plausible mais incorrect)",
      "B": "Option B (correcte)",
      "C": "Option C (distractor)",
      "D": "Option D (distractor)"
    },
    "correct_answer": "B",
    "explanation": "Explication claire pourquoi B est correct"
  }
]

RÈGLES:
1. Réponds UNIQUEMENT avec le JSON, aucun texte avant/après
2. Exactement 8 questions
3. Une seule bonne réponse par question
4. Les distractors doivent être plausibles mais clairement incorrects
5. La bonne réponse doit être répartie aléatoirement (A, B, C, D)
6. Explications concises mais pédagogiques

TEXTE À COUVRIR:
{content}
""",
    'medium': """
Tu es un professeur expert en pédagogie. Génère exactement 8 questions QCM MOYENNES (niveau intermédiaire) 
sur le texte suivant.

INSTRUCTIONS SPÉCIFIQUES NIVEAU MOYEN:
- Compréhension des concepts (pas juste mémorisation)
- Application simple des concepts à des situations
- Liens entre différentes parties du texte
- Différenciation de concepts proches
- Questions nécessitant une compréhension globale du sujet

FORMAT JSON STRICT REQUIS:
[
  {
    "question_text": "Question nécessitant compréhension/application ?",
    "options": {
      "A": "Option plausible",
      "B": "Option plausible",
      "C": "Option correcte",
      "D": "Option plausible"
    },
    "correct_answer": "C",
    "explanation": "Explication détaillée du raisonnement"
  }
]

RÈGLES:
1. Réponds UNIQUEMENT avec le JSON
2. Exactement 8 questions
3. Distractors crédibles (erreurs communes d'étudiants)
4. Questions testant la compréhension, pas la mémorisation
5. Répartition équilibrée des bonnes réponses
6. Explications éducatives

TEXTE À COUVRIR:
{content}
""",
    'hard': """
Tu es un professeur expert en pédagogie. Génère exactement 8 questions QCM DIFFICILES (niveau avancé) 
sur le texte suivant.

INSTRUCTIONS SPÉCIFIQUES NIVEAU DIFFICILE:
- Analyse critique et raisonnement avancé
- Synthese de plusieurs concepts du texte
- Cas pratiques complexes à résoudre
- Questions avec pièges logiques bien construits
- Inférences nécessaires (information implicite)
- Élimination de plusieurs options avant de trouver la bonne

FORMAT JSON STRICT REQUIS:
[
  {
    "question_text": "Question complexe nécessitant analyse et raisonnement ?",
    "options": {
      "A": "Option plausible avec piège logique",
      "B": "Option plausible mais incorrecte",
      "C": "Option correcte après analyse",
      "D": "Option très crédible (distractor fort)"
    },
    "correct_answer": "C",
    "explanation": "Explication détaillée du raisonnement analytique requis"
  }
]

RÈGLES:
1. Réponds UNIQUEMENT avec le JSON
2. Exactement 8 questions de haute qualité analytique
3. Distractors très crédibles (pièges pour étudiants non attentifs)
4. Questions stimulant la réflexion critique
5. Niveau examen ou concours difficile
6. Explications détaillées montrant le raisonnement

TEXTE À COUVRIR:
{content}
"""
}


class PersonalizedExerciseGenerator:
    """Générateur d'exercices QCM personnalisés avec gestion de la difficulté."""

    def __init__(self):
        self.questions_per_exercise = 8

    def generate_for_user(
        self,
        user_id: int,
        summary_id: int,
        difficulty: str,
        seed: int,
        existing_exercise: Optional[UserPersonalizedExercise] = None
    ) -> Tuple[Optional[UserPersonalizedExercise], bool]:
        """
        Génère un exercice personnalisé pour un utilisateur spécifique.

        Args:
            user_id: ID de l'utilisateur
            summary_id: ID du résumé source
            difficulty: 'easy', 'medium', ou 'hard'
            seed: Seed aléatoire pour variation
            existing_exercise: Instance existante à mettre à jour (régénération)

        Returns:
            (exercise, generated_by_ai): Tuple avec l'exercice et le statut IA
        """
        try:
            summary = Summary.objects.get(id=summary_id)

            # Utiliser l'exercice existant ou en créer un nouveau
            if existing_exercise:
                exercise = existing_exercise
                exercise.status = 'generating'
                exercise.difficulty = difficulty
                exercise.seed = seed
                exercise.regenerated_count += 1
                exercise.save()
            else:
                exercise = UserPersonalizedExercise.objects.create(
                    user_id=user_id,
                    summary=summary,
                    difficulty=difficulty,
                    seed=seed,
                    status='generating',
                    questions=[]
                )

            # Générer les questions via IA
            questions_data, generated_by_ai = self._generate_questions(
                summary.texte_resume,
                difficulty,
                seed
            )

            if questions_data:
                exercise.questions = questions_data
                exercise.status = 'completed'
                exercise.generated_by_ai = generated_by_ai
                exercise.save()

                logger.info(
                    f"✅ Exercice perso généré: user={user_id}, summary={summary_id}, "
                    f"difficulty={difficulty}, questions={len(questions_data)}, AI={generated_by_ai}"
                )
                return exercise, generated_by_ai
            else:
                exercise.status = 'failed'
                exercise.save()
                logger.error(f"❌ Échec génération exercice perso pour user={user_id}")
                return None, False

        except Summary.DoesNotExist:
            logger.error(f"Résumé {summary_id} introuvable")
            return None, False
        except Exception as e:
            logger.error(f"Erreur génération exercice perso: {e}")
            if 'exercise' in locals():
                exercise.status = 'failed'
                exercise.save()
            return None, False

    def _generate_questions(
        self,
        resume_text: str,
        difficulty: str,
        seed: int
    ) -> Tuple[Optional[List[Dict]], bool]:
        """
        Génère les questions via DeepSeek ou fallback local.
        """
        # Initialiser le seed pour la variation
        random.seed(seed)

        # Vérifier si DeepSeek est configuré
        if not deepseek_service.is_configured():
            logger.warning("DeepSeek non configuré - fallback local")
            return self._generate_mock_questions(resume_text, difficulty, seed), False

        try:
            # Préparer le prompt selon la difficulté
            template = PROMPT_TEMPLATES.get(difficulty, PROMPT_TEMPLATES['medium'])
            # Tronquer le texte si trop long (DeepSeek a des limites)
            content = resume_text[:8000] if len(resume_text) > 8000 else resume_text
            # NB: .replace() et non .format() car le template contient des accolades JSON littérales
            prompt = template.replace('{content}', content)

            # 🔒 ANTI-TRICHE : injecter le seed dans le prompt pour garantir
            #    des questions UNIQUES par utilisateur (variation forcée par l'IA)
            seed_hint = f"\n\nIMPORTANT - Variante personnelle #{seed} :\n" \
                        f"Génère des questions DIFFÉRENTES de celles données à d'autres étudiants.\n" \
                        f"Utilise des exemples, angles et formulations originaux basés sur ce seed.\n" \
                        f"Ne répète jamais les mêmes questions deux fois pour ce même cours.\n"
            prompt = prompt + seed_hint

            # Appeler DeepSeek
            result = deepseek_service.generate_summary(prompt, max_tokens=2000)

            if result.get('success'):
                questions = self._parse_response(result['content'])
                if questions and len(questions) >= 5:  # Minimum 5 questions valides
                    return questions[:8], True  # Maximum 8 questions
                else:
                    logger.warning("Parsing échoué ou moins de 5 questions - fallback")
                    return self._generate_mock_questions(resume_text, difficulty, seed), False
            else:
                logger.warning(f"DeepSeek échoué: {result.get('error')} - fallback")
                return self._generate_mock_questions(resume_text, difficulty, seed), False

        except Exception as e:
            logger.error(f"Erreur appel DeepSeek: {e}")
            return self._generate_mock_questions(resume_text, difficulty, seed), False

    def _parse_response(self, content: str) -> Optional[List[Dict]]:
        """Parse la réponse JSON de DeepSeek."""
        try:
            # Nettoyer le contenu
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

            questions = json.loads(content)

            # Valider la structure
            valid_questions = []
            for q in questions:
                if self._validate_question(q):
                    valid_questions.append(q)

            return valid_questions if valid_questions else None

        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur validation questions: {e}")
            return None

    def _validate_question(self, question: Dict) -> bool:
        """Valide la structure d'une question."""
        # Normaliser la clé : certains modèles renvoient 'question' au lieu de 'question_text'
        if 'question_text' not in question and 'question' in question:
            question['question_text'] = question['question']

        required_fields = ['question_text', 'options', 'correct_answer', 'explanation']
        if not all(field in question for field in required_fields):
            return False

        options = question['options']
        if not all(opt in options for opt in ['A', 'B', 'C', 'D']):
            return False

        if question['correct_answer'] not in ['A', 'B', 'C', 'D']:
            return False

        return True

    def _generate_mock_questions(
        self,
        resume_text: str,
        difficulty: str,
        seed: int
    ) -> List[Dict]:
        """
        Génère des questions fallback basées sur le contenu réel.
        Variation selon la difficulté demandée.
        """
        import re

        random.seed(seed)

        # Extraire des phrases clés
        sentences = re.split(r'[.!?\n]+', resume_text)
        sentences = [s.strip() for s in sentences if 30 < len(s.strip()) < 300]

        # Extraire des mots-clés
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]{5,}\b', resume_text.lower())
        stop_words = {'dans', 'avec', 'pour', 'sont', 'cette', 'tout', 'mais', 'plus',
                      'comme', 'aussi', 'donc', 'leur', 'leurs', 'nous', 'vous', 'elle',
                      'entre', 'sous', 'sans', 'autre', 'après', 'avant', 'bien', 'alors'}
        keywords = list({w for w in words if w not in stop_words})[:30]
        random.shuffle(keywords)

        questions = []

        # Générer selon la difficulté
        if difficulty == 'easy':
            questions = self._generate_easy_questions(sentences, keywords)
        elif difficulty == 'hard':
            questions = self._generate_hard_questions(sentences, keywords)
        else:  # medium (défaut)
            questions = self._generate_medium_questions(sentences, keywords)

        # Compléter jusqu'à 8 questions si nécessaire
        while len(questions) < 8:
            questions.append(self._generate_generic_question(difficulty, len(questions)))

        return questions[:8]

    def _generate_easy_questions(self, sentences, keywords):
        """Questions faciles factuelles."""
        questions = []

        if sentences:
            # Q1: Définition/Mot clé
            if keywords:
                kw = keywords[0].capitalize()
                others = [k.capitalize() for k in keywords[1:4]] if len(keywords) > 3 else ["Concept", "Idée", "Terme"]
                opts = [kw] + others
                random.shuffle(opts)
                correct = ['A', 'B', 'C', 'D'][opts.index(kw)]
                questions.append({
                    "question_text": f"Quel terme clé est central dans ce cours ?",
                    "options": dict(zip('ABCD', opts)),
                    "correct_answer": correct,
                    "explanation": f"Le terme '{kw}' est essentiel dans ce cours."
                })

            # Q2: Phrase complétion
            if len(sentences) > 0:
                sent = sentences[0][:100]
                questions.append({
                    "question_text": f"Complétez: '{sent}...'",
                    "options": {
                        "A": "C'est une définition correcte",
                        "B": "C'est un exemple concret",
                        "C": "C'est le concept principal",
                        "D": "Aucune de ces réponses"
                    },
                    "correct_answer": "C",
                    "explanation": "Cette phrase introduit le concept principal du cours."
                })

        return questions

    def _generate_medium_questions(self, sentences, keywords):
        """Questions moyennes compréhension."""
        questions = []

        # Q1: Compréhension concept
        if len(sentences) >= 2:
            questions.append({
                "question_text": "Quel est l'objectif principal de ce cours ?",
                "options": {
                    "A": "Mémoriser des dates et noms",
                    "B": "Comprendre et appliquer les concepts fondamentaux",
                    "C": "Apprendre par cœur sans comprendre",
                    "D": "Étudier uniquement la théorie"
                },
                "correct_answer": "B",
                "explanation": "Le vrai apprentissage vise la compréhension et l'application."
            })

        # Q2: Lien entre concepts
        if len(keywords) >= 2:
            questions.append({
                "question_text": f"Comment '{keywords[0]}' et '{keywords[1]}' sont-ils liés ?",
                "options": {
                    "A": "Ils sont complètement indépendants",
                    "B": "Ils sont interconnectés dans ce cours",
                    "C": "Ils s'opposent l'un à l'autre",
                    "D": "Ils n'ont aucun rapport"
                },
                "correct_answer": "B",
                "explanation": f"Ces concepts sont liés et se complètent dans le cours."
            })

        return questions

    def _generate_hard_questions(self, sentences, keywords):
        """Questions difficiles analyse."""
        questions = []

        # Q1: Analyse critique
        questions.append({
            "question_text": "Quelle conclusion peut-on tirer de l'analyse de ce cours ?",
            "options": {
                "A": "La théorie est suffisante sans pratique",
                "B": "L'application pratique est essentielle à la maîtrise",
                "C": "La mémorisation suffit pour réussir",
                "D": "Le cours n'a pas d'application réelle"
            },
            "correct_answer": "B",
            "explanation": "L'analyse montre que la pratique est indispensable pour maîtriser le sujet."
        })

        # Q2: Synthèse
        if keywords:
            questions.append({
                "question_text": f"Si on applique '{keywords[0]}' dans un cas complexe, qu'arrive-t-il ?",
                "options": {
                    "A": "Cela ne fonctionne pas du tout",
                    "B": "Cela nécessite une adaptation et une analyse",
                    "C": "Cela fonctionne exactement comme dans le cours",
                    "D": "C'est impossible à appliquer"
                },
                "correct_answer": "B",
                "explanation": "L'application réelle demande toujours adaptation et réflexion critique."
            })

        return questions

    def _generate_generic_question(self, difficulty, index):
        """Question générique de fallback."""
        templates = {
            'easy': [
                ("Quelle est la notion principale abordée ?", "B", "La notion principale est au cœur du cours."),
                ("Quel élément est essentiel à retenir ?", "A", "Cet élément est fondamental pour comprendre le sujet."),
            ],
            'medium': [
                ("Quelle compétence ce cours vise-t-il à développer ?", "B", "Le cours vise le développement de compétences pratiques."),
                ("Comment les concepts s'organisent-ils ?", "C", "Les concepts forment un ensemble cohérent et structuré."),
            ],
            'hard': [
                ("Quelle analyse critique ce sujet mérite-t-il ?", "B", "Une analyse critique révèle les nuances et implications profondes."),
                ("Comment ce concept évolue-t-il dans des contextes complexes ?", "C", "L'évolution du concept dépend du contexte et des applications."),
            ]
        }

        pool = templates.get(difficulty, templates['medium'])
        q_text, correct, expl = pool[index % len(pool)]

        # Générer options aléatoires
        opts = ["Concept A", "Concept B", "Concept C", "Concept D"]
        random.shuffle(opts)
        correct_letter = ['A', 'B', 'C', 'D'][opts.index("Concept B")]

        return {
            "question_text": q_text,
            "options": dict(zip('ABCD', opts)),
            "correct_answer": correct_letter,
            "explanation": expl
        }


# Instance singleton
generator = PersonalizedExerciseGenerator()


def generate_personalized_exercise(
    user_id: int,
    summary_id: int,
    difficulty: str,
    seed: int,
    existing_exercise=None
):
    """Fonction utilitaire pour générer un exercice personnalisé."""
    return generator.generate_for_user(
        user_id, summary_id, difficulty, seed, existing_exercise
    )
