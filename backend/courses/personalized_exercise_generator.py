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
from typing import List, Dict, Optional, Tuple
from .models import Summary, UserPersonalizedExercise, UserPersonalizedQuestion
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

# Titres de sections purement structurels des résumés (pas des notions) :
# inutilisables comme terme cible d'une question de sens.
STRUCTURAL_TITLES = {
    'introduction', 'introduction simple', 'idée principale', 'idée principale du cours',
    'petit résumé final', 'petit résumé', 'résumé final', 'mini-glossaire', 'conclusion',
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
                    status='generating'
                )

            # Générer les questions via IA
            questions_data, generated_by_ai = self._generate_questions(
                summary.texte_resume,
                summary.titre,
                difficulty,
                seed
            )

            # Répartir les bonnes réponses de façon équilibrée et non
            # prévisible (jamais 3 de suite identiques, pas de blocs A/A/A
            # puis B/B/B…) SANS changer le contenu ni le contrat : on ne
            # permute que l'affectation des options aux lettres A/B/C/D.
            if questions_data:
                questions_data = self._rebalance_correct_answers(questions_data, seed)

            if questions_data:
                # Structure 3 tables (comme le standard) : chaque question est
                # une ligne séparée rattachée à l'exercice. En régénération,
                # on remplace les lignes existantes par les nouvelles.
                exercise.questions.all().delete()
                UserPersonalizedQuestion.objects.bulk_create([
                    UserPersonalizedQuestion(
                        personalized_exercise=exercise,
                        question_text=q.get('question_text') or q.get('question', ''),
                        options=q.get('options', {}),
                        correct_answer=q.get('correct_answer', 'A'),
                        explanation=q.get('explanation', ''),
                        code_language=q.get('code_language'),
                        code_block=q.get('code_block'),
                        order=idx,
                    )
                    for idx, q in enumerate(questions_data)
                ])
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
            reason = 'DeepSeek non configuré (clé API absente)'
            logger.warning(f"⚠️ [QCM Perso Génération] {reason} → fallback local utilisé (origin=fallback_local, difficulty={difficulty}, seed={seed})")
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
                    logger.info(f"✅ [QCM Perso Génération] {len(questions)} questions issues de DEEPSEEK (origin=deepseek, difficulty={difficulty}, seed={seed})")
                    return questions[:8], True  # Maximum 8 questions
                else:
                    reason = 'parsing JSON échoué' if not questions else f'seulement {len(questions)} questions valides (< 5)'
                    logger.warning(f"⚠️ [QCM Perso Génération] DeepSeek a répondu mais {reason} → fallback local utilisé (origin=fallback_local, difficulty={difficulty}, seed={seed})")
                    return self._generate_mock_questions(resume_text, difficulty, seed), False
            else:
                reason = result.get('error', 'erreur inconnue')
                logger.warning(f"⚠️ [QCM Perso Génération] ÉCHEC DeepSeek: {reason} → fallback local utilisé (origin=fallback_local, difficulty={difficulty}, seed={seed})")
                return self._generate_mock_questions(resume_text, difficulty, seed), False

        except Exception as e:
            reason = f'{type(e).__name__}: {str(e)}'
            logger.error(f"❌ [QCM Perso Génération] EXCEPTION appel DeepSeek: {reason} → fallback local utilisé (origin=fallback_local, difficulty={difficulty}, seed={seed})")
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

        # Questions génériques « à trous » ou « laquelle de ces affirmations »
        # (règles du prompt : vraies questions de compréhension uniquement).
        # NB : « Complétez le code/la formule » reste autorisé (complétion technique réelle).
        generic_stems = [
            'complétez cette phrase', 'complétez la phrase', 'complète la phrase',
            'complétez cette idée', 'complétez l\'idée', 'complétez la définition',
            'complétez cette définition', 'complétez cette notion', 'complétez cette expression',
            'complétez avec la valeur', 'complétez le mot', 'complétez le terme',
            'complétez le bon mot', 'remplissez le trou', 'le mot manquant',
            'laquelle de ces affirmations', 'quelle de ces affirmations',
            'parmi ces affirmations', 'parmi les affirmations',
            'laquelle de ces propositions', 'parmi les propositions',
            'quelle affirmation est', 'quelle est la bonne affirmation',
        ]
        for g in generic_stems:
            if g in question_text:
                logger.warning(f"Question générique détectée: '{question['question_text']}' — question rejetée")
                return False

        # Questions de RECONNAISSANCE de phrase (mémoriser une phrase EXACTE du
        # résumé, sans comprendre) : interdites — elles ne testent aucune
        # connaissance précise.
        recognition_phrases = [
            "d'après le résumé, quelle phrase",
            "selon le résumé, quelle phrase",
            "d'après le résultat, quelle phrase",
            "selon le contenu, quelle affirmation",
            "d'après ce qui est présenté, quelle affirmation",
            "quelle phrase du résumé",
            "quelle phrase parle",
            "quelle phrase décrit",
            "quelle phrase correspond",
            "quelle phrase évoque",
            "quelle phrase se rapporte",
            "quelle phrase concerne",
            "quelle phrase est tirée",
            "quelle phrase de la leçon",
            "correspond au schéma",
            "que signifie cette phrase",
        ]
        for r in recognition_phrases:
            if r in question_text:
                logger.warning(f"Question de reconnaissance de phrase détectée: '{question['question_text']}' — question rejetée")
                return False

        return True

    # ═══════════════════════════════════════════════════════════════════════════
    #  RÉPARTITION ÉQUILIBRÉE ET NON PRÉVISIBLE DES BONNES RÉPONSES
    #  Aucun changement de contenu ni de contrat : on ne permute que
    #  l'affectation des options aux lettres A/B/C/D et on recalcule
    #  `correct_answer` en conséquence. La bonne réponse garde donc son texte,
    #  mais à une position équilibrée sur l'ensemble du QCM.
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _letters():
        return ['A', 'B', 'C', 'D']

    @staticmethod
    def _current_letters(questions):
        letters = PersonalizedExerciseGenerator._letters()
        return [
            (q.get('correct_answer') if q.get('correct_answer') in letters else 'A')
            for q in questions
        ]

    def _needs_rebalance(self, questions):
        """True si la distribution actuelle est prévisible (3 mêmes de suite,
        déséquilibre marqué entre les lettres, ou alternance régulière)."""
        seq = self._current_letters(questions)
        n = len(seq)
        if n < 3:
            return False
        # 3 fois de suite la même lettre
        for i in range(2, n):
            if seq[i] == seq[i - 1] == seq[i - 2]:
                return True
        # Déséquilibre : écart > 1 entre la lettre la plus et la moins utilisée
        counts = {l: seq.count(l) for l in self._letters()}
        if max(counts.values()) - min(counts.values()) > 1:
            return True
        # Alternance régulière A/B/A/B… (motif prévisible)
        if n >= 6 and len(set(seq)) == 2:
            if all(seq[i] == seq[i % 2] for i in range(n)):
                return True
        return False

    def _move_correct_answer_to(self, question, target_letter):
        """
        Replace la bonne réponse (contenu inchangé) sous la lettre cible et
        recalcule correct_answer. Les distracteurs sont répartis sur les autres
        lettres.
        """
        options = question.get('options')
        if not isinstance(options, dict):
            return question
        current = question.get('correct_answer')
        if current not in options or target_letter not in self._letters():
            return question
        correct_text = options[current]
        other_values = [v for k, v in options.items() if k != current]
        remaining = [l for l in self._letters() if l != target_letter]
        new_options = {target_letter: correct_text}
        # Python conserve l'ordre d'insertion des dicts : la répartition des
        # distracteurs sur les lettres restantes est stable.
        for letter, text in zip(remaining, other_values):
            new_options[letter] = text
        question['options'] = new_options
        question['correct_answer'] = target_letter
        return question

    def _rebalance_correct_answers(self, questions, seed=None):
        """
        Répartit les bonnes réponses de façon équilibrée (≈ parts égales
        A/B/C/D) et non prévisible (jamais 3 de suite identiques). N'intervient
        que si la distribution actuelle est prévisible ou trop regroupée : dans
        le cas courant (déjà variée), le contenu n'est pas touché.
        """
        if not questions or not self._needs_rebalance(questions):
            return questions

        n = len(questions)
        # Seed dérivé mais distinct du seed de contenu : la distribution reste
        # reproductible par exercice sans recopier celle d'un autre étudiant.
        rng = random.Random((seed or 0) + 1000003)
        letters = self._letters()

        # Quota cible : parts égales (le reste réparti aléatoirement).
        counts = {l: n // 4 for l in letters}
        for l in rng.sample(letters, n % 4):
            counts[l] += 1

        # Construit une séquence équilibrée, sans 3 répétitions consécutives,
        # en privilégiant toujours les lettres au quota restant le plus élevé.
        seq = []
        for _ in range(n):
            usable = [
                l for l in letters
                if counts[l] > 0
                and not (len(seq) >= 2 and seq[-1] == l and seq[-2] == l)
            ]
            if not usable:
                usable = [l for l in letters if counts[l] > 0]
            best = max(counts[l] for l in usable)
            candidates = [l for l in usable if counts[l] == best]
            chosen = rng.choice(candidates)
            counts[chosen] -= 1
            seq.append(chosen)

        questions = [self._move_correct_answer_to(q, target) for q, target in zip(questions, seq)]
        logger.info(f"🔀 [QCM Répartition] Bonnes réponses rééquilibrées ({len(seq)} questions) : {''.join(seq)}")
        return questions

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
        résumé. Aucune question générique « à trous » (Complétez cette phrase…)
        ni « Laquelle de ces affirmations… » : les questions portent sur le sens
        réel des notions (définitions, idées à retenir, importance) et sur les
        extraits techniques réels (code / formules LaTeX). Variation selon la
        difficulté et le seed.
        """
        questions = []

        if not resume_text or len(resume_text.strip()) < 50:
            logger.warning("Fallback: résumé trop court pour générer des questions réelles")
            return questions

        random.seed(seed)

        # ── Extraction des éléments réels du résumé ────────────────────────────
        # Structure markdown du résumé (## Notion : titre + sous-parties pédagogiques)
        sections = self._extract_sections(resume_text)

        # Phrases significatives
        sentences = [s.strip() for s in re.split(r'[.!?\n]+', resume_text) if 40 < len(s.strip()) < 250]

        # Termes réels (mots longs non triviaux)
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]{5,}\b', resume_text.lower())
        terms = list(dict.fromkeys(w for w in words if w not in STOP_WORDS))
        # Termes "nom plausibles" (précédés d'un article) pour les questions de repérage
        noun_terms = [t for t in terms if self._looks_like_noun(t, resume_text)] or terms

        # Extraits de code réels (blocs ```langage ... ```)
        code_blocks = re.findall(r'```(\w+)?\s*\n([\s\S]*?)```', resume_text)
        # TACHE2 (formules) : extraire aussi les formules LaTeX $$...$$ du résumé.
        # Elles deviennent des blocs techniques de langage "latex" → zone grisée côté Flutter.
        latex_blocks = [('latex', c.strip()) for c in re.findall(r'\$\$(.*?)\$\$', resume_text, re.DOTALL)]
        code_blocks = code_blocks + latex_blocks

        # Définitions réelles (sections structurées + mini-glossaire + phrases « X est … »)
        defs = self._collect_real_definitions(resume_text, sections, sentences)

        # Dédoublonnage PAR TEXTE de question : l'ordre des options variant à chaque
        # essai, deux questions identiques peuvent différer (impossible d'utiliser
        # l'égalité des dicts). Deux questions au même énoncé sont écartées.
        seen_texts = set()

        def add_unique(q):
            if not q:
                return False
            key = (q.get('question_text') or q.get('question', '')).strip().lower()
            if key in seen_texts:
                return False
            seen_texts.add(key)
            questions.append(q)
            return True

        # 1. Question sur un extrait technique réel (code / formule) — au plus 1
        if code_blocks:
            add_unique(self._build_code_question(code_blocks[0], terms))

        # 2. Questions réelles de compréhension, ordonnées selon la difficulté
        builders_by_difficulty = {
            'easy': ['meaning', 'retenir', 'importance'],
            'medium': ['meaning', 'retenir', 'importance'],
            'hard': ['meaning', 'retenir', 'importance'],
        }
        builder_order = builders_by_difficulty.get(difficulty, builders_by_difficulty['medium'])

        # Au maximum 2 questions par type pour garantir un mélange varié
        builder_counts = {}
        for builder_key in builder_order:
            for _ in range(6):
                if len(questions) >= 8:
                    break
                if builder_counts.get(builder_key, 0) >= 2:
                    break
                q = None
                if builder_key == 'meaning':
                    q = self._build_meaning_question(defs)
                elif builder_key == 'retenir':
                    q = self._build_retenir_question(sections)
                elif builder_key == 'importance':
                    q = self._build_importance_question(sections)
                if add_unique(q):
                    builder_counts[builder_key] = builder_counts.get(builder_key, 0) + 1

        # 3. Compléter si nécessaire (jamais de questions inventées) : d'abord de
        #    vraies questions de sens, puis « quelle phrase parle de X ? »
        if len(questions) < 8:
            for _ in range(10):
                if len(questions) >= 8:
                    break
                add_unique(self._build_meaning_question(defs))
                if len(questions) < 8:
                    add_unique(self._build_about_question(sentences, noun_terms))

        logger.info(f"📄 [QCM Perso Fallback] {len(questions)} questions construites depuis le contenu réel (difficulty={difficulty}, seed={seed})")
        return questions[:8]

    def _extract_sections(self, resume_text):
        """
        Parse la structure markdown d'un résumé : sections `## Titre` avec leurs
        sous-parties pédagogiques réelles (**Définition simple**, **À retenir**,
        **Pourquoi c'est important** ...). Retourne [{title, definition, retenir, why}].
        """
        sections = []
        current = None
        for raw in resume_text.splitlines():
            line = raw.strip()
            if not line:
                continue
            m = re.match(r'^#{1,4}\s+(.+)$', line)
            if m:
                if current is not None:
                    sections.append(current)
                current = {'title': m.group(1).strip(), 'definition': None, 'retenir': None, 'why': None}
                continue
            if current is None:
                continue
            lm = re.match(r'^[-*>\s]*\*\*(.+?)\*\*\s*:\s*(.+)$', line)
            if lm:
                label = lm.group(1).strip().lower()
                content = lm.group(2).strip()
                if 'définition' in label or 'definition' in label:
                    current['definition'] = current['definition'] or content
                elif 'retenir' in label:
                    current['retenir'] = current['retenir'] or content
                elif 'important' in label:
                    current['why'] = current['why'] or content
        if current is not None:
            sections.append(current)
        return [s for s in sections if s['title']]

    def _clean_notation_title(self, title):
        """Nettoie un titre de section : « Notion 1 : l'héritage » → « l'héritage »."""
        t = re.sub(r'^Notion\s*\d+\s*:\s*', '', title, flags=re.I).strip()
        return t.strip('*').strip()

    def _looks_like_noun(self, term, resume_text):
        """
        Heuristique simple : un terme ressemble à un nom s'il apparaît précédé
        d'un déterminant (le, la, les, un, une, des, du, de la, l', d'...).
        Évite de capturer des adjectifs isolés (« magiques sont… », « réelle »).
        NB : l'apostrophe est collée au terme (« l'héritage ») — pas d'espace.
        """
        pattern = re.compile(
            r'(?i)\b(?:le |la |les |un |une |des |du |de la |de l\'|l\'|d\')' + re.escape(term) + r'\b'
        )
        return bool(pattern.search(resume_text))

    def _collect_real_definitions(self, resume_text, sections, sentences):
        """
        Collecte des paires (terme, définition) RÉELLEMENT présentes dans le
        résumé : sections structurées (« Définition simple »), mini-glossaire
        (« - **terme** : définition ») et phrases définitionnelles (« X est … »).
        """
        defs = []
        seen = set()

        def add(term, definition):
            term = term.strip().strip('*').strip()
            definition = definition.strip()
            if not term or not definition or len(definition) < 10:
                return
            if term.lower() in STOP_WORDS:
                return
            if len(term) > 48:  # un terme-cible trop long ferait une question illisible
                return
            key = (term.lower(), definition[:40].lower())
            if key in seen:
                return
            seen.add(key)
            defs.append((term, definition))

        # 1) Notions structurées : section → « Définition simple »
        for sec in sections:
            title = self._clean_notation_title(sec['title'])
            if any(s in title.lower() for s in STRUCTURAL_TITLES):
                continue
            if sec.get('definition'):
                add(title, sec['definition'])

        # 2) Mini-glossaire / « - **terme** : définition »
        skip_labels = {
            'définition simple', 'definition simple', 'explication facile', 'analogie',
            'exemple concret', "pourquoi c'est important", 'pourquoi c’est important',
            'à retenir', 'a retenir', 'pourquoi c est important',
        }
        for m in re.finditer(r'[-*>\s]*\*\*([A-Za-zÀ-ÿ][\w\s\-]{1,40}?)\*\*\s*:\s*(.+)', resume_text):
            label = m.group(1).strip().lower()
            if label in skip_labels or 'définition' in label or 'definition' in label:
                continue
            add(m.group(1).strip(), m.group(2).strip())

        # 3) Phrases définitionnelles réelles : « X est ... », « X désigne ... »,
        #    « X permet ... », « X sert à ... » — X doit ressembler à un nom
        #    (précédé d'un article) pour ne pas capturer un adjectif de liste
        #    (« ... et les méthodes magiques sont ... »).
        for sent in sentences:
            for m in re.finditer(
                r'\b([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-]{2,})\s+(?:est|sont|représente|représentent|désigne|désignent|signifie|correspond|permet|sert)\s+',
                sent
            ):
                term = m.group(1)
                if not self._looks_like_noun(term, resume_text):
                    continue
                add(term, sent)
                break
        return defs

    def _build_meaning_question(self, defs):
        """
        Vraie question de sens : « D'après le résumé, que signifie X ? »
        avec de réelles définitions du résumé en options (jamais de phrase à trous).
        """
        if not defs or len(defs) < 4:
            return None
        target_term, target_def = random.choice(defs)
        distractors = [d for (t, d) in defs if t.lower() != target_term.lower()]
        distractors = list(dict.fromkeys(distractors))
        if len(distractors) < 3:
            return None
        options_list = [target_def] + random.sample(distractors, 3)
        random.shuffle(options_list)
        correct_letter = [k for k, v in zip('ABCD', options_list) if v == target_def][0]
        # Adapter le verbe à la définition réelle : « X permet/sert … » → « que permet X ? »
        if re.search(r'\bpermet\b|\bsert\b', target_def.lower()):
            stem = f"Selon le résumé, que permet « {target_term} » ?"
        else:
            stem = f"D'après le résumé, que signifie « {target_term} » ?"
        return {
            "question_text": stem,
            "options": dict(zip('ABCD', options_list)),
            "correct_answer": correct_letter,
            "explanation": f"Dans le résumé, « {target_term} » est présenté ainsi : « {target_def} »",
        }

    def _build_about_question(self, sentences, terms):
        """
        Question de repérage (secours pour les résumés non structurés) :
        « D'après le résumé, quelle phrase parle de X ? ». La bonne réponse est
        une phrase RÉELLE du résumé qui mentionne X, les distracteurs sont
        d'autres phrases réelles du résumé (jamais inventées).
        """
        if len(sentences) < 4 or not terms:
            return None
        random.shuffle(sentences)
        sample_terms = random.sample(terms, min(len(terms), 8))
        for term in sample_terms:
            candidates = [s for s in sentences if term.lower() in s.lower()]
            others = [s for s in sentences if term.lower() not in s.lower()]
            if not candidates or len(others) < 3:
                continue
            target = random.choice(candidates)
            options_list = [target] + random.sample(others, 3)
            random.shuffle(options_list)
            correct_letter = [k for k, v in zip('ABCD', options_list) if v == target][0]
            return {
                "question_text": f"D'après le résumé, quelle phrase parle de « {term} » ?",
                "options": dict(zip('ABCD', options_list)),
                "correct_answer": correct_letter,
                "explanation": f"Dans le résumé, « {term} » apparaît dans cette phrase : « {target} »",
            }
        return None

    def _build_retenir_question(self, sections):
        """
        Vraie question de synthèse : « Quelle idée faut-il retenir à propos de X ? »
        avec de vraies phrases « À retenir » du résumé en options.
        """
        retenirs = []
        for sec in sections:
            title = self._clean_notation_title(sec['title'])
            if any(s in title.lower() for s in STRUCTURAL_TITLES):
                continue
            if sec.get('retenir') and len(sec['retenir']) >= 8:
                retenirs.append((title, sec['retenir']))
        if len(retenirs) < 4:
            return None
        target_title, target_text = random.choice(retenirs)
        distractors = [r for (t, r) in retenirs if t.lower() != target_title.lower()]
        distractors = list(dict.fromkeys(distractors))
        if len(distractors) < 3:
            return None
        options_list = [target_text] + random.sample(distractors, 3)
        random.shuffle(options_list)
        correct_letter = [k for k, v in zip('ABCD', options_list) if v == target_text][0]
        return {
            "question_text": f"Quelle est l'idée essentielle à retenir à propos de « {target_title} » selon le résumé ?",
            "options": dict(zip('ABCD', options_list)),
            "correct_answer": correct_letter,
            "explanation": f"Le résumé indique à retenir à propos de « {target_title} » : « {target_text} »",
        }

    def _build_importance_question(self, sections):
        """
        Vraie question de compréhension : « Pourquoi X est-il important ? »
        avec de vraies raisons données dans le résumé (« Pourquoi c'est important »).
        """
        whys = []
        for sec in sections:
            title = self._clean_notation_title(sec['title'])
            if any(s in title.lower() for s in STRUCTURAL_TITLES):
                continue
            if sec.get('why') and len(sec['why']) >= 8:
                whys.append((title, sec['why']))
        if len(whys) < 4:
            return None
        target_title, target_text = random.choice(whys)
        distractors = [w for (t, w) in whys if t.lower() != target_title.lower()]
        distractors = list(dict.fromkeys(distractors))
        if len(distractors) < 3:
            return None
        options_list = [target_text] + random.sample(distractors, 3)
        random.shuffle(options_list)
        correct_letter = [k for k, v in zip('ABCD', options_list) if v == target_text][0]
        return {
            "question_text": f"Selon le résumé, pourquoi « {target_title} » est-il important ?",
            "options": dict(zip('ABCD', options_list)),
            "correct_answer": correct_letter,
            "explanation": f"Le résumé explique l'importance de « {target_title} » ainsi : « {target_text} »",
        }

    def _build_code_question(self, code_block, terms):
        """
        Question sur un extrait technique réel du résumé (code ou formule LaTeX) :
        on interroge sur un élément réellement présent dans l'extrait, avec des
        distracteurs réels (autres éléments de l'extrait ou termes du résumé).

        TACHE2 : renvoie code_language/code_block pour que la zone grisée
        s'affiche côté Flutter (comme le générateur standard). Le contenu brut
        est donc retiré du question_text (affiché dans la zone grisée).
        """
        language, code = code_block
        is_formula = language and language.lower() in ('latex', 'formula', 'math')
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
        if is_formula:
            return {
                "question_text": "Quelle expression est utilisée dans cette formule tirée du résumé ?",
                "options": dict(zip('ABCD', options_list)),
                "correct_answer": correct_letter,
                "explanation": f"L'expression « {target} » apparaît dans la formule tirée du résumé.",
                "code_language": "latex",
                "code_block": code,
            }
        return {
            "question_text": "Quelle instruction est utilisée dans cet extrait de code tiré du résumé ?",
            "options": dict(zip('ABCD', options_list)),
            "correct_answer": correct_letter,
            "explanation": f"L'instruction « {target} » apparaît dans l'extrait de code du résumé.",
            "code_language": language or None,
            "code_block": code,
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
