"""
Générateur d'exercices QCM personnalisés avec niveaux de difficulté.
Chaque utilisateur reçoit des questions uniques pour chaque résumé.

La logique de génération (voie IA et fallback local) reprend celle du générateur
standard `exercise_generator` — considérée comme la référence validée :
- Voie IA : réutilise deepseek_service.generate_exercises (prompt pédagogique
  détaillé, contenu réel du résumé injecté, options issues du contenu).
- Fallback local : questions construites UNIQUEMENT à partir du contenu réel
  du résumé (phrases, termes, valeurs, code). Aucune question générique,
  aucun placeholder, aucun concept inventé.
"""
import json
import random
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from .models import Summary, UserPersonalizedExercise
from .deepseek_service import deepseek_service

logger = logging.getLogger(__name__)

# Mots trop génériques pour servir d'options réelles dans le fallback local
STOP_WORDS = {
    'dans', 'avec', 'pour', 'sont', 'cette', 'tout', 'mais', 'plus',
    'comme', 'aussi', 'donc', 'leur', 'leurs', 'nous', 'vous', 'elle',
    'entre', 'sous', 'sans', 'autre', 'après', 'avant', 'bien', 'alors',
    'être', 'avoir', 'faire', 'cours', 'texte', 'résumé', 'peut', 'très',
    'elles', 'ils', 'aux', 'des', 'une', 'sur', 'titre', 'leçon',
    'chapitre', 'quand', 'ainsi', 'enfin', 'pendant', 'plusieurs',
    'différent', 'différents', 'même', 'toute', 'tous', 'toutes', 'avec',
    'cela', 'ça', 'cette', 'celui', 'celle', 'leurs', 'aucun', 'aucune',
    'chaque', 'quelques', 'certains', 'certaines', 'autres', 'où', 'quoi',
    'dont', 'dans', 'selon', 'afin', 'environ', 'notamment', 'ainsi',
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
                summary.titre,
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
        titre: str,
        difficulty: str,
        seed: int
    ) -> Tuple[Optional[List[Dict]], bool]:
        """
        Génère les questions via DeepSeek ou fallback local.
        La voie IA réutilise le prompt validé du générateur standard
        (deepseek_service.generate_exercises) avec la variante seed anti-triche.
        """
        # Initialiser le seed pour la variation
        random.seed(seed)

        # Vérifier si DeepSeek est configuré
        if not deepseek_service.is_configured():
            logger.warning("DeepSeek non configuré - fallback local")
            return self._generate_mock_questions(resume_text, difficulty, seed), False

        try:
            # Réutiliser le prompt IA validé du générateur standard :
            # questions et options issues du contenu réel du résumé
            result = deepseek_service.generate_exercises(
                resume_text,
                titre,
                difficulty=difficulty,
                seed=seed
            )

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
        """
        Valide la structure d'une question et rejette les placeholders et les
        questions artificielles (logique de validation du générateur standard).
        """
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

        # Détection de placeholders génériques dans les options
        placeholder_patterns = ['concept a', 'concept b', 'concept c', 'concept d',
                                'option a', 'option b', 'option c', 'option d',
                                'réponse a', 'réponse b', 'réponse c', 'réponse d',
                                'notion a', 'notion b', 'notion c', 'notion d',
                                'terme a', 'terme b', 'terme c', 'terme d']
        for opt in ['A', 'B', 'C', 'D']:
            opt_text = str(options.get(opt, '')).lower()
            if any(p in opt_text for p in placeholder_patterns):
                logger.warning(f"Placeholder détecté dans option {opt}: '{options[opt]}' — question rejetée")
                return False
            if len(opt_text.strip()) < 3:
                logger.warning(f"Option {opt} trop courte: '{options[opt]}' — question rejetée")
                return False

        # Détection des questions artificielles interdites (règles du prompt)
        question_text = str(question.get('question_text', '')).lower()
        artificial_patterns = [
            'parmi les concepts', 'parmi les notions', 'parmi les termes',
            'parmi les idées', 'parmi les options',
            'quel concept est correct', 'que signifie le concept',
            'que veut dire le concept', 'quel est le concept principal',
            'quel concept est central', 'quel terme est central',
            'quel terme est essentiel', 'quelle est la notion principale',
            'quel terme est lié', 'quel est le terme clé',
        ]
        for p in artificial_patterns:
            if p in question_text:
                logger.warning(f"Question artificielle détectée: '{question['question_text']}' — question rejetée")
                return False

        return True

    # ═══════════════════════════════════════════════════════════════════════════
    #  FALLBACK LOCAL : questions construites UNIQUEMENT sur le contenu réel
    #  (même logique que le fallback du générateur standard). Aucune question
    #  générique ni inventée : si le contenu est insuffisant, on renvoie moins
    #  de questions plutôt que d'en inventer.
    # ═══════════════════════════════════════════════════════════════════════════

    def _generate_mock_questions(
        self,
        resume_text: str,
        difficulty: str,
        seed: int
    ) -> List[Dict]:
        """
        Génère des questions fallback UNIQUEMENT à partir du contenu réel du
        résumé : phrases complétées avec de vrais termes, affirmations exactes
        avec des faits altérés (distracteurs réels), valeurs numériques réelles,
        extraits de code réels. Variation selon la difficulté et le seed.
        """
        questions = []

        if not resume_text or len(resume_text.strip()) < 50:
            logger.warning("Fallback: résumé trop court pour générer des questions réelles")
            return questions

        random.seed(seed)

        # ── Extraction des éléments réels du résumé ────────────────────────────
        # Phrases significatives
        sentences = [s.strip() for s in re.split(r'[.!?\n]+', resume_text) if 40 < len(s.strip()) < 250]

        # Termes réels (mots longs non triviaux) — utilisés comme options réelles
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]{5,}\b', resume_text.lower())
        terms = list(dict.fromkeys(w for w in words if w not in STOP_WORDS))

        # Nombres réels présents dans le résumé
        numbers = re.findall(
            r'\b\d+(?:[.,]\d+)?\s*(?:%|€|\$|FCFA|ans|jours|mois|heures|min|s|km|m|cm|g|kg|Mo|Go|Hz|V)\b|\b\d+(?:[.,]\d+)?\b',
            resume_text
        )

        # Extraits de code réels (blocs ```langage ... ```)
        code_blocks = re.findall(r'```(\w+)?\s*\n([\s\S]*?)```', resume_text)

        random.shuffle(sentences)

        # Ordre des types de questions selon la difficulté
        builders_by_difficulty = {
            'easy': ['definition', 'completion', 'statement', 'number', 'code'],
            'medium': ['completion', 'statement', 'definition', 'number', 'code'],
            'hard': ['statement', 'definition', 'completion', 'code', 'number'],
        }
        builder_order = builders_by_difficulty.get(difficulty, builders_by_difficulty['medium'])

        # Au maximum 2 questions par type pour garantir un mélange varié
        builder_counts = {}
        for builder_key in builder_order:
            for sentence in sentences:
                if len(questions) >= 8:
                    break
                if builder_counts.get(builder_key, 0) >= 2:
                    break
                q = None
                if builder_key == 'definition':
                    q = self._build_definition_question(sentence, terms)
                elif builder_key == 'completion':
                    q = self._build_completion_question(sentence, terms)
                elif builder_key == 'statement':
                    q = self._build_statement_question(sentence, terms)
                if q:
                    questions.append(q)
                    builder_counts[builder_key] = builder_counts.get(builder_key, 0) + 1

        # Question sur une valeur numérique réelle (si le résumé en contient)
        if len(numbers) >= 4 and len(questions) < 6:
            q = self._build_number_question(numbers, sentences)
            if q:
                questions.append(q)

        # Question sur un extrait de code réel (si le résumé en contient)
        if code_blocks and len(questions) < 7:
            q = self._build_code_question(code_blocks[0], terms)
            if q:
                questions.append(q)

        # Compléter si nécessaire avec d'autres phrases du résumé (jamais inventées)
        if len(questions) < 8:
            for sentence in sentences:
                if len(questions) >= 8:
                    break
                q = self._build_completion_question(sentence, terms)
                if q and q not in questions:
                    questions.append(q)

        return questions[:8]

    def _pick_real_options(self, target, terms, count=4):
        """Construit les options avec le terme réel cible + d'autres termes réels du résumé."""
        distractors = [t for t in terms if t.lower() != target.lower()]
        if len(distractors) < count - 1:
            return None
        options_list = [target] + random.sample(distractors, count - 1)
        random.shuffle(options_list)
        return options_list

    def _build_definition_question(self, sentence, terms):
        """
        Question de définition : « ___ est ... » avec un terme réel du résumé,
        distracteurs = autres termes réels du résumé.
        """
        if not terms:
            return None
        # Chercher un motif de définition réel : « X est ... », « X désigne ... », etc.
        match = re.search(
            r'\b([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-]{2,})\s+(?:est|sont|représente|représentent|désigne|désignent|signifie|correspond à)\s+',
            sentence
        )
        if not match:
            return None
        target = match.group(1)
        if target.lower() in STOP_WORDS or target.lower() not in [t.lower() for t in terms]:
            return None
        blanked = sentence.replace(target, '___', 1)
        options_list = self._pick_real_options(target, terms, count=4)
        if not options_list:
            return None
        correct_letter = [k for k, v in zip('ABCD', options_list) if v == target][0]
        return {
            "question_text": f"Complétez la définition tirée du résumé : « {blanked} »",
            "options": dict(zip('ABCD', options_list)),
            "correct_answer": correct_letter,
            "explanation": f"Le terme « {target} » est défini ainsi dans le résumé : « {sentence} »",
        }

    def _build_completion_question(self, sentence, terms):
        """
        Question de complétion : une phrase réelle du résumé avec un mot réel
        masqué, distracteurs = d'autres termes réels du résumé.
        """
        if not terms:
            return None
        candidates = [w for w in sentence.split() if len(w) > 4 and w.lower() not in STOP_WORDS]
        if not candidates:
            return None
        target = random.choice(candidates)
        options_list = self._pick_real_options(target, terms, count=4)
        if not options_list:
            return None
        blanked = sentence.replace(target, '___', 1)
        correct_letter = [k for k, v in zip('ABCD', options_list) if v == target][0]
        return {
            "question_text": f"Complétez la phrase extraite du résumé : « {blanked} »",
            "options": dict(zip('ABCD', options_list)),
            "correct_answer": correct_letter,
            "explanation": f"La phrase du résumé contient bien le mot « {target} » : « {sentence} »",
        }

    def _mutate_sentence(self, sentence, terms):
        """
        Altère une phrase réelle en remplaçant un de ses mots importants par un
        autre terme réel du résumé → affirmations fausses mais crédibles.
        """
        words = sentence.split()
        candidates = [w for w in words if len(w) > 5 and w.lower() not in STOP_WORDS]
        random.shuffle(candidates)
        for target in candidates:
            replacements = [t for t in terms if t.lower() != target.lower() and t not in words]
            if not replacements:
                continue
            replacement = random.choice(replacements)
            return sentence.replace(target, replacement, 1)
        return None

    def _build_statement_question(self, sentence, terms):
        """
        Question d'affirmation : la bonne réponse est une phrase RÉELLE du résumé,
        les distracteurs sont cette même phrase avec un fait altéré par un autre
        terme réel du résumé (jamais d'affirmation générique).
        """
        if not terms:
            return None
        distractors = []
        for _ in range(6):
            mutated = self._mutate_sentence(sentence, terms)
            if mutated and mutated != sentence and mutated not in distractors:
                distractors.append(mutated)
            if len(distractors) >= 3:
                break
        if len(distractors) < 3:
            return None
        options_list = [sentence] + distractors
        random.shuffle(options_list)
        correct_letter = [k for k, v in zip('ABCD', options_list) if v == sentence][0]
        return {
            "question_text": "Laquelle de ces affirmations correspond au contenu du résumé ?",
            "options": dict(zip('ABCD', options_list)),
            "correct_answer": correct_letter,
            "explanation": f"Cette affirmation est directement tirée du résumé : « {sentence} »",
        }

    def _build_number_question(self, numbers, sentences):
        """
        Question sur une valeur numérique réelle du résumé : la phrase avec la
        valeur masquée, options = de vraies valeurs présentes dans le résumé.
        """
        distinct_numbers = list(dict.fromkeys(numbers))
        if len(distinct_numbers) < 4:
            return None
        # Trouver une phrase contenant un des nombres
        for sentence in sentences:
            num_match = re.search(
                r'\b\d+(?:[.,]\d+)?\s*(?:%|€|\$|FCFA|ans|jours|mois|heures|min|s|km|m|cm|g|kg|Mo|Go|Hz|V)?\b',
                sentence
            )
            if not num_match:
                continue
            target = num_match.group(0).strip()
            if target not in distinct_numbers:
                continue
            blanked = sentence.replace(target, '___', 1)
            options_list = random.sample(distinct_numbers, 4)
            if target not in options_list:
                options_list[random.randint(0, 3)] = target
            random.shuffle(options_list)
            correct_letter = [k for k, v in zip('ABCD', options_list) if v == target][0]
            return {
                "question_text": f"Complétez avec la valeur réellement indiquée dans le résumé : « {blanked} »",
                "options": dict(zip('ABCD', options_list)),
                "correct_answer": correct_letter,
                "explanation": f"Le résumé indique bien la valeur « {target} » : « {sentence} »",
            }
        return None

    def _build_code_question(self, code_block, terms):
        """
        Question sur un extrait de code réel du résumé : on interroge sur une
        instruction réellement présente dans l'extrait, avec des distracteurs
        réels (autres instructions du code ou termes du résumé).
        """
        language, code = code_block
        tokens = list(dict.fromkeys(re.findall(r'[a-zA-Z_]\w*', code)))
        tokens = [t for t in tokens if len(t) > 1][:8]
        if not tokens:
            return None
        # Combiner avec les termes réels du résumé pour avoir assez d'options
        pool = tokens + [t for t in terms if t.lower() not in [x.lower() for x in tokens]]
        if len(pool) < 4:
            return None
        target = random.choice(tokens)
        options_list = [target] + random.sample(
            [p for p in pool if p.lower() != target.lower()], 3
        )
        random.shuffle(options_list)
        correct_letter = [k for k, v in zip('ABCD', options_list) if v == target][0]
        return {
            "question_text": f"Voici un extrait de code tiré du résumé :\n{code}\nQuelle instruction est utilisée dans cet extrait ?",
            "options": dict(zip('ABCD', options_list)),
            "correct_answer": correct_letter,
            "explanation": f"L'instruction « {target} » apparaît dans l'extrait de code du résumé.",
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
