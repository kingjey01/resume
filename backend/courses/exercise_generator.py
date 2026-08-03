"""
Service de génération d'exercices QCM via DeepSeekService
Utilise le même service DeepSeek que la génération de résumés (deepseek_service.py)
"""
import json
from .models import Exercise, ExerciseQuestion, Summary
from .deepseek_service import deepseek_service
import logging

logger = logging.getLogger(__name__)

class ExerciseGenerator:
    """Générateur d'exercices QCM basé sur les résumés, via DeepSeekService"""
    
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
            logger.warning("DeepSeek non configuré — utilisation du fallback local pour les exercices")
            return self._generate_mock_questions(titre, resume_text, difficulty=difficulty), False
        
        try:
            # Appeler DeepSeekService.generate_exercises (même pattern que generate_summary)
            result = deepseek_service.generate_exercises(resume_text, titre, difficulty=difficulty)

            if result['success']:
                # Parser la réponse JSON de DeepSeek
                parsed = self._parse_ai_response(result['content'])
                if parsed and len(parsed) >= 5:
                    logger.info(f"✅ {len(parsed)} questions générées par DeepSeek IA pour: {titre}")
                    return parsed, True
                else:
                    reason = 'Parsing échoué' if not parsed else f"Seulement {len(parsed)} questions valides (< 5)"
                    logger.warning(f"⚠️ {reason} pour la réponse DeepSeek, fallback local")
                    return self._generate_mock_questions(titre, resume_text, difficulty=difficulty), False
            else:
                logger.warning(f"⚠️ Échec DeepSeek exercices: {result['error']} — fallback local")
                return self._generate_mock_questions(titre, resume_text, difficulty=difficulty), False

        except Exception as e:
            logger.error(f"Erreur lors de l'appel DeepSeek pour exercices: {str(e)}")
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
        Génère des questions basées sur le contenu réel du résumé.
        Si le texte est disponible, extrait des phrases clés pour créer des QCM pertinents.
        Adapte la difficulté selon le paramètre (easy/medium/hard).
        """
        import re, random

        questions = []
        
        # Paramètres de difficulté
        difficulty_config = {
            'easy': {'distractor_similarity': 'low', 'question_complexity': 'basic'},
            'medium': {'distractor_similarity': 'medium', 'question_complexity': 'applied'},
            'hard': {'distractor_similarity': 'high', 'question_complexity': 'advanced'},
        }
        config = difficulty_config.get(difficulty, difficulty_config['medium'])

        if resume_text and len(resume_text.strip()) > 100:
            # Extraire les phrases significatives du résumé (>40 chars, pas trop longues)
            sentences = re.split(r'[.!?\n]+', resume_text)
            sentences = [s.strip() for s in sentences if 40 < len(s.strip()) < 200]

            # Extraire les mots-clés (mots de plus de 5 lettres, non communs)
            stop_words = {'dans', 'avec', 'pour', 'sont', 'cette', 'tout', 'mais', 'plus',
                          'comme', 'aussi', 'donc', 'leur', 'leurs', 'nous', 'vous', 'elle',
                          'entre', 'sous', 'sans', 'autre', 'après', 'avant', 'bien'}
            all_words = re.findall(r'\b[a-zA-ZÀ-ÿ]{5,}\b', resume_text)
            keywords = list({w.lower() for w in all_words if w.lower() not in stop_words})
            random.shuffle(keywords)
            keywords = keywords[:20]

            # Question 1 — phrase clé réelle (complétion)
            if len(sentences) >= 1:
                phrase = sentences[0]
                # Trouver un mot important à "cacher"
                words_in_phrase = [w for w in phrase.split() if len(w) > 4]
                if words_in_phrase:
                    target = random.choice(words_in_phrase)
                    blanked = phrase.replace(target, '___', 1)
                    distractors = [kw.capitalize() for kw in keywords if kw.lower() != target.lower()][:3]
                    while len(distractors) < 3:
                        distractors.append("Aucune de ces réponses")
                    options_list = [target.capitalize()] + distractors
                    random.shuffle(options_list)
                    correct_letter = [k for k, v in zip('ABCD', options_list) if v == target.capitalize()][0]
                    questions.append({
                        "question": f"Complétez la phrase : « {blanked} »",
                        "options": dict(zip('ABCD', options_list)),
                        "correct_answer": correct_letter,
                        "explanation": f"La phrase correcte mentionne « {target} » dans le contexte de {titre}."
                    })

            # Question 2 — phrase clé réelle (vrai/faux enrichi)
            if len(sentences) >= 2:
                phrase = sentences[1]
                questions.append({
                    "question": f"Laquelle de ces affirmations correspond au résumé de « {titre} » ?",
                    "options": {
                        "A": phrase,
                        "B": f"Le cours traite uniquement des aspects historiques de {titre}.",
                        "C": f"Le résumé ne mentionne aucun concept pratique.",
                        "D": f"Ce cours est sans rapport avec {titre}."
                    },
                    "correct_answer": "A",
                    "explanation": f"Cette affirmation est directement tirée du résumé de {titre}."
                })

            # Question 3 — mot-clé du contenu
            if len(keywords) >= 4:
                kw = keywords[0].capitalize()
                others = [k.capitalize() for k in keywords[1:4]]
                options_list = [kw] + others
                random.shuffle(options_list)
                correct_letter = [k for k, v in zip('ABCD', options_list) if v == kw][0]
                questions.append({
                    "question": f"Quel terme est central dans le résumé de « {titre} » ?",
                    "options": dict(zip('ABCD', options_list)),
                    "correct_answer": correct_letter,
                    "explanation": f"Le terme « {kw} » est l'un des concepts clés abordés dans ce résumé."
                })

            # Question 4 — phrase 3 si disponible
            if len(sentences) >= 3:
                phrase = sentences[2]
                words_in_phrase = [w for w in phrase.split() if len(w) > 4]
                if words_in_phrase:
                    target = random.choice(words_in_phrase)
                    distractors = [kw.capitalize() for kw in keywords if kw.lower() != target.lower()][:3]
                    while len(distractors) < 3:
                        distractors.append("Aucun des termes ci-dessus")
                    options_list = [target.capitalize()] + distractors
                    random.shuffle(options_list)
                    correct_letter = [k for k, v in zip('ABCD', options_list) if v == target.capitalize()][0]
                    questions.append({
                        "question": f"Dans le contexte de « {titre} », quel mot correspond à : « {phrase[:80]}... » ?",
                        "options": dict(zip('ABCD', options_list)),
                        "correct_answer": correct_letter,
                        "explanation": f"Le terme « {target} » apparaît dans cette partie du résumé."
                    })

            # Question 5 — synthèse sur le contenu
            if len(sentences) >= 1:
                questions.append({
                    "question": f"Quel est l'objectif principal du cours « {titre} » selon le résumé ?",
                    "options": {
                        "A": f"Comprendre et maîtriser les concepts fondamentaux de {titre}",
                        "B": "Mémoriser des définitions sans les comprendre",
                        "C": "Étudier uniquement les aspects théoriques sans application",
                        "D": "Aucun objectif pédagogique n'est défini"
                    },
                    "correct_answer": "A",
                    "explanation": f"Le résumé vise à faire comprendre et maîtriser les concepts fondamentaux de {titre}."
                })

        # Fallback si pas assez de contenu extrait (toujours atteindre 5 questions)
        fallback_pool = [
            {
                "question": f"Quel est le domaine principal couvert par « {titre} » ?",
                "options": {"A": "Les fondements théoriques et pratiques", "B": "L'histoire ancienne uniquement", "C": "Les mathématiques pures", "D": "La philosophie abstraite"},
                "correct_answer": "A",
                "explanation": f"Le cours « {titre} » couvre ses fondements théoriques et pratiques."
            },
            {
                "question": f"Comment utiliser les connaissances de « {titre} » en pratique ?",
                "options": {"A": "Seulement en classe", "B": "Dans des contextes professionnels et académiques", "C": "Jamais en dehors des examens", "D": "Uniquement pour la recherche avancée"},
                "correct_answer": "B",
                "explanation": "Ces connaissances sont applicables dans de nombreux contextes professionnels et académiques."
            },
            {
                "question": f"Quelle compétence ce cours « {titre} » vise-t-il principalement à développer ?",
                "options": {"A": "La mémorisation mécanique", "B": "L'analyse critique et la compréhension", "C": "La copie de documents", "D": "L'évitement des sujets complexes"},
                "correct_answer": "B",
                "explanation": f"Le cours « {titre} » vise à développer l'analyse critique et la compréhension profonde."
            },
            {
                "question": f"Quel niveau de difficulté correspond au cours « {titre} » ?",
                "options": {"A": "Aucune difficulté particulière", "B": "Progressif, du simple au complexe", "C": "Exclusivement pour experts", "D": "Aléatoire sans structure"},
                "correct_answer": "B",
                "explanation": "Un bon cours progresse du simple au complexe pour faciliter l'apprentissage."
            },
            {
                "question": f"Pourquoi est-il important de maîtriser les concepts de « {titre} » ?",
                "options": {"A": "Pour satisfaire uniquement les exigences formelles", "B": "Pour pouvoir les appliquer dans des situations réelles", "C": "Pour les oublier après l'examen", "D": "Pour impressionner les pairs uniquement"},
                "correct_answer": "B",
                "explanation": f"Maîtriser « {titre} » permet d'appliquer ces concepts dans des situations réelles concrètes."
            },
        ]
        fallback_idx = 0
        while len(questions) < 5 and fallback_idx < len(fallback_pool):
            questions.append(fallback_pool[fallback_idx])
            fallback_idx += 1

        return questions[:7]


def generate_exercises_for_summary(summary_id, existing_exercise=None, difficulty='medium'):
    """Fonction utilitaire pour générer des exercices"""
    generator = ExerciseGenerator()
    return generator.generate_exercises_for_summary(summary_id, existing_exercise=existing_exercise, difficulty=difficulty)
