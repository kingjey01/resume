"""
Service de génération d'exercices QCM via DeepSeekService
Utilise le même service DeepSeek que la génération de résumés (deepseek_service.py)
"""
import json
import random
import re
from .models import Exercise, ExerciseQuestion, Summary
from .deepseek_service import deepseek_service
import logging

logger = logging.getLogger(__name__)

class ExerciseGenerator:
    """Générateur d'exercices QCM basé sur les résumés, via DeepSeekService"""

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

    def __init__(self):
        pass
        
    def generate_exercises_for_summary(self, summary_id, existing_exercise=None, difficulty='medium'):
        """
        Génère 5-10 exercices QCM pour un résumé donné.
        Si existing_exercise est fourni, l'utilise directement (évite la double création).
        difficulty: 'easy', 'medium', 'hard'
        """
        try:
            summary = Summary.objects.get(id=summary_id)

            # Utiliser l'exercice existant ou en créer un nouveau
            if existing_exercise:
                exercise = existing_exercise
            else:
                exercise = Exercise.objects.create(
                    summary=summary,
                    titre=f"Exercices - {summary.titre}",
                    description=f"Questions à choix multiples basées sur le résumé: {summary.titre}",
                    status='generating'
                )
            
            # Générer les questions via DeepSeekService (même service que les résumés)
            questions_data, generated_by_ai = self._generate_questions_with_ai(summary.texte_resume, summary.titre, difficulty=difficulty)
            
            if questions_data:
                # Créer les questions
                for i, question_data in enumerate(questions_data, 1):
                    ExerciseQuestion.objects.create(
                        exercise=exercise,
                        question_text=question_data['question'],
                        option_a=question_data['options']['A'],
                        option_b=question_data['options']['B'],
                        option_c=question_data['options']['C'],
                        option_d=question_data['options']['D'],
                        correct_answer=question_data['correct_answer'],
                        explanation=question_data.get('explanation', ''),
                        code_language=question_data.get('code_language'),
                        code_block=question_data.get('code_block'),
                        order=i
                    )
                
                exercise.difficulty = difficulty
                exercise.status = 'completed'
                exercise.generated_by_ai = generated_by_ai
                exercise.save()
                
                logger.info(f"Exercice généré avec succès pour le résumé {summary_id}: {len(questions_data)} questions (IA: {generated_by_ai})")
                return exercise
            else:
                exercise.status = 'failed'
                exercise.generated_by_ai = generated_by_ai
                exercise.save()
                logger.error(f"Échec de génération des questions pour le résumé {summary_id}")
                return None
                
        except Summary.DoesNotExist:
            logger.error(f"Résumé {summary_id} introuvable")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'exercices: {str(e)}")
            if 'exercise' in locals():
                exercise.status = 'failed'
                exercise.save()
            return None
    
    def _generate_questions_with_ai(self, resume_text, titre, difficulty='medium'):
        """
        Génère les questions via DeepSeekService (même service que les résumés).
        Retourne (questions_data, generated_by_ai).
        """
        # Vérifier si DeepSeek est configuré (même logique que pour les résumés)
        if not deepseek_service.is_configured():
            reason = 'DeepSeek non configuré (clé API absente)'
            logger.warning(f"⚠️ [QCM Génération] {reason} → fallback local utilisé (origin=fallback_local)")
            return self._generate_mock_questions(titre, resume_text, difficulty=difficulty), False

        try:
            # Appeler DeepSeekService.generate_exercises (même pattern que generate_summary)
            result = deepseek_service.generate_exercises(resume_text, titre, difficulty=difficulty)

            if result['success']:
                # Parser la réponse JSON de DeepSeek
                parsed = self._parse_ai_response(result['content'])
                if parsed and len(parsed) >= 5:
                    logger.info(f"✅ [QCM Génération] {len(parsed)} questions issues de DEEPSEEK (origin=deepseek, difficulty={difficulty}) pour: {titre}")
                    return parsed, True
                else:
                    reason = 'parsing JSON échoué' if not parsed else f'seulement {len(parsed)} questions valides (< 5)'
                    logger.warning(f"⚠️ [QCM Génération] DeepSeek a répondu mais {reason} → fallback local utilisé (origin=fallback_local)")
                    return self._generate_mock_questions(titre, resume_text, difficulty=difficulty), False
            else:
                reason = result.get('error', 'erreur inconnue')
                logger.warning(f"⚠️ [QCM Génération] ÉCHEC DeepSeek: {reason} → fallback local utilisé (origin=fallback_local)")
                return self._generate_mock_questions(titre, resume_text, difficulty=difficulty), False

        except Exception as e:
            reason = f'{type(e).__name__}: {str(e)}'
            logger.error(f"❌ [QCM Génération] EXCEPTION appel DeepSeek: {reason} → fallback local utilisé (origin=fallback_local)")
            return self._generate_mock_questions(titre, resume_text, difficulty=difficulty), False
    
    def _parse_ai_response(self, content):
        """Parse la réponse de l'IA"""
        try:
            # Nettoyer le contenu pour extraire le JSON
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            questions = json.loads(content)
            
            # Valider la structure
            validated_questions = []
            for q in questions:
                if self._validate_question_structure(q):
                    validated_questions.append(q)
            
            return validated_questions[:10]  # Maximum 10 questions
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur de validation des questions: {str(e)}")
            return None
    
    def _validate_question_structure(self, question):
        """Valide la structure d'une question et détecte les placeholders"""
        required_fields = ['question', 'options', 'correct_answer']

        if not all(field in question for field in required_fields):
            return False

        options = question['options']
        if not all(opt in options for opt in ['A', 'B', 'C', 'D']):
            return False

        if question['correct_answer'] not in ['A', 'B', 'C', 'D']:
            return False

        # Détection de placeholders génériques
        placeholder_patterns = ['concept a', 'concept b', 'concept c', 'concept d',
                                   'option a', 'option b', 'option c', 'option d',
                                   'réponse a', 'réponse b', 'réponse c', 'réponse d']
        for opt in ['A', 'B', 'C', 'D']:
            opt_text = str(options.get(opt, '')).lower()
            if any(p in opt_text for p in placeholder_patterns):
                logger.warning(f"Placeholder détecté dans option {opt}: '{options[opt]}' — question rejetée")
                return False
            if len(opt_text.strip()) < 3:
                logger.warning(f"Option {opt} trop courte: '{options[opt]}' — question rejetée")
                return False

        return True
    
    def _generate_mock_questions(self, titre, resume_text=None, difficulty='medium'):
        """
        Fallback local : questions construites UNIQUEMENT à partir du contenu
        réel du résumé (phrases, termes, valeurs numériques, extraits de code).
        Aucune question générique, aucun placeholder, aucun concept inventé :
        si le contenu est insuffisant, on renvoie moins de questions plutôt
        que d'en inventer. La difficulté change le type de questions privilégié.
        Même logique que le fallback validé du générateur personnalisé.
        """
        if not resume_text or len(resume_text.strip()) < 50:
            logger.warning("📄 [QCM Fallback] Résumé trop court pour générer des questions réelles — 0 question")
            return []

        # ── Extraction des éléments réels du résumé ────────────────────────────
        sentences = [s.strip() for s in re.split(r'[.!?\n]+', resume_text) if 40 < len(s.strip()) < 250]

        words = re.findall(r'\b[a-zA-ZÀ-ÿ]{5,}\b', resume_text.lower())
        terms = list(dict.fromkeys(w for w in words if w not in self.STOP_WORDS))

        numbers = re.findall(
            r'\b\d+(?:[.,]\d+)?\s*(?:%|€|\$|FCFA|ans|jours|mois|heures|min|s|km|m|cm|g|kg|Mo|Go|Hz|V)\b|\b\d+(?:[.,]\d+)?\b',
            resume_text
        )

        code_blocks = re.findall(r'```(\w+)?\s*\n([\s\S]*?)```', resume_text)
        # TACHE2 (formules) : extraire aussi les formules LaTeX $$...$$ du résumé.
        # Elles deviennent des blocs techniques de langage "latex" → zone grisée côté Flutter.
        latex_blocks = [('latex', c.strip()) for c in re.findall(r'\$\$(.*?)\$\$', resume_text, re.DOTALL)]
        code_blocks = code_blocks + latex_blocks

        random.shuffle(sentences)

        # Ordre des types de questions selon la difficulté demandée
        builders_by_difficulty = {
            'easy': ['definition', 'completion', 'statement', 'number', 'code'],
            'medium': ['completion', 'statement', 'definition', 'number', 'code'],
            'hard': ['statement', 'definition', 'completion', 'code', 'number'],
        }
        builder_order = builders_by_difficulty.get(difficulty, builders_by_difficulty['medium'])

        questions = []
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

        logger.info(f"📄 [QCM Fallback] {len(questions)} questions construites depuis le contenu réel (difficulty={difficulty})")
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
        """Question de définition : « ___ est ... » avec un terme réel du résumé."""
        if not terms:
            return None
        match = re.search(
            r'\b([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-]{2,})\s+(?:est|sont|représente|représentent|désigne|désignent|signifie|correspond à)\s+',
            sentence
        )
        if not match:
            return None
        target = match.group(1)
        if target.lower() in self.STOP_WORDS or target.lower() not in [t.lower() for t in terms]:
            return None
        blanked = sentence.replace(target, '___', 1)
        options_list = self._pick_real_options(target, terms, count=4)
        if not options_list:
            return None
        correct_letter = [k for k, v in zip('ABCD', options_list) if v == target][0]
        return {
            "question": f"Complétez la définition tirée du résumé : « {blanked} »",
            "options": dict(zip('ABCD', options_list)),
            "correct_answer": correct_letter,
            "explanation": f"Le terme « {target} » est défini ainsi dans le résumé : « {sentence} »",
        }

    def _build_completion_question(self, sentence, terms):
        """Question de complétion : une phrase réelle du résumé avec un mot réel masqué."""
        if not terms:
            return None
        candidates = [w for w in sentence.split() if len(w) > 4 and w.lower() not in self.STOP_WORDS]
        if not candidates:
            return None
        target = random.choice(candidates)
        options_list = self._pick_real_options(target, terms, count=4)
        if not options_list:
            return None
        blanked = sentence.replace(target, '___', 1)
        correct_letter = [k for k, v in zip('ABCD', options_list) if v == target][0]
        return {
            "question": f"Complétez la phrase extraite du résumé : « {blanked} »",
            "options": dict(zip('ABCD', options_list)),
            "correct_answer": correct_letter,
            "explanation": f"La phrase du résumé contient bien le mot « {target} » : « {sentence} »",
        }

    def _mutate_sentence(self, sentence, terms):
        """Altère une phrase réelle en remplaçant un mot important par un autre terme réel."""
        words = sentence.split()
        candidates = [w for w in words if len(w) > 5 and w.lower() not in self.STOP_WORDS]
        random.shuffle(candidates)
        for target in candidates:
            replacements = [t for t in terms if t.lower() != target.lower() and t not in words]
            if not replacements:
                continue
            replacement = random.choice(replacements)
            return sentence.replace(target, replacement, 1)
        return None

    def _build_statement_question(self, sentence, terms):
        """Question d'affirmation : bonne réponse = phrase RÉELLE du résumé, distracteurs = mêmes phrases altérées."""
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
            "question": "Laquelle de ces affirmations correspond au contenu du résumé ?",
            "options": dict(zip('ABCD', options_list)),
            "correct_answer": correct_letter,
            "explanation": f"Cette affirmation est directement tirée du résumé : « {sentence} »",
        }

    def _build_number_question(self, numbers, sentences):
        """Question sur une valeur numérique réelle : phrase avec la valeur masquée, options = vraies valeurs du résumé."""
        distinct_numbers = list(dict.fromkeys(numbers))
        if len(distinct_numbers) < 4:
            return None
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
                "question": f"Complétez avec la valeur réellement indiquée dans le résumé : « {blanked} »",
                "options": dict(zip('ABCD', options_list)),
                "correct_answer": correct_letter,
                "explanation": f"Le résumé indique bien la valeur « {target} » : « {sentence} »",
            }
        return None

    def _build_code_question(self, code_block, terms):
        """Question sur un extrait technique réel du résumé (code ou formule LaTeX), avec distracteurs réels."""
        language, code = code_block
        is_formula = language and language.lower() in ('latex', 'formula', 'math')
        tokens = list(dict.fromkeys(re.findall(r'[a-zA-Z_]\w*', code)))
        tokens = [t for t in tokens if len(t) > 1][:8]
        if not tokens:
            return None
        pool = tokens + [t for t in terms if t.lower() not in [x.lower() for x in tokens]]
        if len(pool) < 4:
            return None
        target = random.choice(tokens)
        options_list = [target] + random.sample(
            [p for p in pool if p.lower() != target.lower()], 3
        )
        random.shuffle(options_list)
        correct_letter = [k for k, v in zip('ABCD', options_list) if v == target][0]
        if is_formula:
            return {
                "question": "Quelle expression est utilisée dans cette formule tirée du résumé ?",
                "options": dict(zip('ABCD', options_list)),
                "correct_answer": correct_letter,
                "explanation": f"L'expression « {target} » apparaît dans la formule tirée du résumé.",
                "code_language": "latex",
                "code_block": code,
            }
        return {
            "question": "Quelle instruction est utilisée dans cet extrait de code tiré du résumé ?",
            "options": dict(zip('ABCD', options_list)),
            "correct_answer": correct_letter,
            "explanation": f"L'instruction « {target} » apparaît dans l'extrait de code du résumé.",
            "code_language": language or None,
            "code_block": code,
        }


def generate_exercises_for_summary(summary_id, existing_exercise=None, difficulty='medium'):
    """Fonction utilitaire pour générer des exercices"""
    generator = ExerciseGenerator()
    return generator.generate_exercises_for_summary(summary_id, existing_exercise=existing_exercise, difficulty=difficulty)
