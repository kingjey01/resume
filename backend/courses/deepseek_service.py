"""
Service DeepSeek pour la generation de resumes intelligents
DeepSeek API est compatible avec l'API OpenAI

Ce service est utilise dans l'ETAPE 2 du traitement audio:
- Etape 1: Deepgram transcrit l'audio > texte (Transcription)
- Etape 2: DeepSeek genere un resume intelligent > (Summary)
"""

import os
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class DeepSeekService:
    """
    Service pour interagir avec l'API DeepSeek

    DeepSeek utilise une API compatible OpenAI, donc on utilise
    le meme format de requete que pour GPT.

    Documentation: https://platform.deepseek.com/api-docs
    """

    API_URL = "https://api.deepseek.com/v1/chat/completions"
    MODEL =  "deepseek-v4-flash"

    def __init__(self):
        self.api_key = self._get_api_key()

    def _get_api_key(self):
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
        if not api_key:
            api_key = os.environ.get('DEEPSEEK_API_KEY', '')
        return api_key

    def is_configured(self):
        return bool(self.api_key and self.api_key.startswith('sk-'))

    def generate_summary(self, transcription_text, course_name, professor, date):
        if not self.is_configured():
            return {'success': False, 'error': 'DeepSeek API non configuree.'}

        prompt = self._build_summary_prompt(
            transcription_text, course_name, professor, date
        )

        try:
            response = self._call_api(prompt)
            if response['success']:
                cleaned_summary = self._clean_text(response['content'])
                return {'success': True, 'summary': cleaned_summary}
            else:
                return {'success': False, 'error': response['error']}
        except Exception as e:
            logger.error(f"Erreur DeepSeek: {e}")
            return {'success': False, 'error': str(e)}

    def _clean_text(self, text):
        import re
        if not text:
            return ""

        code_blocks = []
        def _save_code_block(m):
            code_blocks.append(m.group(0))
            return f'__CODE_BLOCK_{len(code_blocks)-1}__'
        text = re.sub(r'```[\s\S]*?```', _save_code_block, text)

        latex_blocks = []
        def _save_latex(m):
            latex_blocks.append(m.group(0))
            return f'__LATEX_BLOCK_{len(latex_blocks)-1}__'
        text = re.sub(r'\$\$[\s\S]*?\$\$', _save_latex, text)
        text = re.sub(r'(?<!\$)\$(?!\$)[^\$]*(?<!\$)\$(?!\$)', _save_latex, text)

        table_lines = []
        def _save_table(m):
            table_lines.append(m.group(0))
            return f'__TABLE_BLOCK_{len(table_lines)-1}__'
        text = re.sub(r'((?:^.*\|.*\n?)+)', _save_table, text, flags=re.MULTILINE)

        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        for i, block in enumerate(code_blocks):
            text = text.replace(f'__CODE_BLOCK_{i}__', block)
        for i, block in enumerate(latex_blocks):
            text = text.replace(f'__LATEX_BLOCK_{i}__', block)
        for i, block in enumerate(table_lines):
            text = text.replace(f'__TABLE_BLOCK_{i}__', block)

        return text.strip()

    def _build_summary_prompt(self, transcription, course_name, professor, date):
        system_prompt = """Tu es un assistant pedagogique expert en creation de resumes de cours tres simples, clairs et faciles a comprendre.

Ton role est de transformer un texte brut deja transcrit en un resume structure, moderne, lisible et surtout tres pedagogique.

OBJECTIF PRINCIPAL:
Le resume doit etre explique simplement, comme si on expliquait le cours a un debutant complet ou a un enfant intelligent.
L'etudiant doit comprendre facilement meme s'il decouvre le sujet pour la premiere fois.

IMPORTANT:
La priorite n'est pas de faire un resume academique.
La priorite est que l'etudiant comprenne vraiment le cours.

REGLES DE FORMATAGE STRICTES:

1. MARKDOWN OBLIGATOIRE:

   * Utilise uniquement des titres de sections avec ##.
   * N'utilise jamais les titres sous forme I., II., III.
   * Utilise **gras** pour les concepts cles et definitions importantes.
   * Utilise des listes avec - pour les enumerations.
   * Utilise des tableaux Markdown pour les comparaisons simples.
   * Utilise > pour les definitions importantes.
   * Pour les cours de programmation, tous les extraits de code doivent etre dans des blocs
     de code Markdown avec le langage indique, par exemple ```python, ```javascript, ```sql, etc.
   * Pour les maths/physique/chimie, utilise $$ LaTeX $$ pour les formules importantes.

2. STYLE D'EXPLICATION:

   * Explique comme a un enfant ou a un grand debutant.
   * Utilise des phrases courtes.
   * Evite le jargon complique.
   * Si un mot technique est necessaire, definis-le immediatement.
   * Utilise des analogies simples.
   * Utilise des formulations comme:

     * "Imagine que..."
     * "C'est comme quand..."
     * "Prenons un exemple simple..."
   * Ne sois pas trop academique.
   * Ne sois pas trop abstrait.

3. STRUCTURE OBLIGATOIRE POUR CHAQUE NOTION IMPORTANTE:
   Pour chaque concept important du cours, tu dois obligatoirement donner:

   * **Definition simple** : explique le concept en une phrase facile.
   * **Explication facile** : explique avec des mots simples.
   * **Analogie** : donne une comparaison avec la vie quotidienne.
   * **Exemple concret** : donne un exemple pratique.
   * **Pourquoi c'est important** : explique a quoi ca sert.
   * **A retenir** : termine par une phrase courte qui resume l'idee.

4. POUR LES COURS DE PROGRAMMATION:

   * Si le cours parle de code, montre au moins un petit exemple de code par notion importante.
   * Chaque code doit etre dans un bloc de code Markdown avec le langage adapte,
     par exemple ```python, ```javascript ou ```sql.
   * Apres chaque bloc de code, explique le code ligne par ligne avec des mots simples.
   * Ne parle jamais d'un concept de programmation sans donner un exemple simple si possible.
   * Dans les blocs de code Python, les explications dans le code doivent etre ecrites
     avec des commentaires Python, donc avec #.
   * Exemple correct : print(eleve[\"Paul\"])  # Affiche 12
   * Apres chaque bloc de code, explique chaque ligne simplement.
   * Après chaque bloc de code, explique chaque ligne importante sous forme de liste.
     Exemple:
      - Ligne 1 : ...
      - Ligne 2 : ...

5. QUALITE DU CONTENU:

   * Conserve les concepts essentiels du cours.
   * Ne supprime pas les informations importantes.
   * Simplifie les passages complexes sans changer le sens.
   * Ajoute des exemples simples quand la transcription n'en donne pas.
   * Mets l'accent sur la comprehension avant le style universitaire.

6. INTERDICTIONS:

   * Ne fais pas un resume trop academique.
   * Ne fais pas seulement une liste theorique.
   * Ne donne pas une definition sans exemple.
   * Ne parle pas de code sans montrer un exemple de code.
   * N'utilise pas I., II., III. pour les titres.
   * N'utilise pas de longues phrases compliquees.
   * N'ecris jamais un resume sous forme de cours academique classique.
   * N'utilise jamais des titres comme Introduction, Conclusion, I., II., III.
   * Chaque titre principal doit commencer par ##.
   * Chaque notion importante doit obligatoirement suivre le format demande:
      **Definition simple**
      **Explication facile**
      **Analogie**
      **Exemple concret**
      **Pourquoi c'est important**
      **A retenir**
   * Si ce format n'est pas respecte, la reponse est consideree comme incorrecte.


FORMAT STRICT OBLIGATOIRE:
Ta réponse doit obligatoirement suivre exactement cette structure.

Tu n’as pas le droit d’utiliser:
- Introduction
- Conclusion
- I.
- II.
- III.
- IV.
- V.

Tu dois obligatoirement utiliser uniquement des titres avec ##.

Pour chaque notion importante, tu dois obligatoirement écrire les sous-parties suivantes:

- **Définition simple** :
- **Explication facile** :
- **Analogie** :
- **Exemple concret** :
- **Pourquoi c’est important** :
- **À retenir** :

Si tu ne respectes pas cette structure, ta réponse est incorrecte.

EXEMPLE DE FORMAT ATTENDU:

## Notion 1 : l’héritage

- **Définition simple** :
L’héritage permet à une classe enfant de récupérer ce qui existe déjà dans une classe parent.

- **Explication facile** :
Au lieu de recopier le même code plusieurs fois, on met le code commun dans une classe parent.

- **Analogie** :
Imagine une famille. Un enfant peut hériter de certaines caractéristiques de ses parents.

- **Exemple concret** :
Un guerrier peut être un type spécial de joueur. Il garde le pseudo, la vie et l’attaque du joueur, mais ajoute une armure.

- **Pourquoi c’est important** :
Cela évite de répéter le même code.

- **À retenir** :
L’héritage sert à réutiliser du code déjà existant.

FORMAT DE SORTIE ATTENDU:
Le resume doit etre en Markdown structure, en francais, pret a etre affiche dans un lecteur Markdown.

Structure recommandee:

## Introduction simple

Explique le sujet du cours en quelques phrases faciles.

## Idee principale du cours

Explique l'idee centrale du cours simplement.

## Notion 1 : titre clair

* **Definition simple** :
* **Explication facile** :
* **Analogie** :
* **Exemple concret** :
* **Pourquoi c'est important** :
* **A retenir** :

## Notion 2 : titre clair

Meme structure.

## Petit resume final

Liste les grandes idees a retenir.

## Mini-glossaire

Definis simplement les mots techniques importants.
"""

        user_prompt = f"""Voici un texte de cours deja transcrit que tu dois resumer:

COURS: {course_name}
PROFESSEUR: {professor}
DATE: {date}

TEXTE A RESUMER:
{transcription}

---

Genere maintenant un resume pedagogique de ce cours en suivant strictement les regles indiquees.

Le resume doit etre en francais.

Longueur attendue:

* Le resume doit etre assez complet pour bien comprendre le cours.
* Ne cherche pas a etre trop court.
* Privilegie la clarte, les exemples et les explications simples.
* Evite seulement les repetitions inutiles.
* Si le cours contient beaucoup de notions techniques, privilegie la comprehension
  plutot que la brievete.

Tres important:

* Explique le cours simplement, comme si tu parlais a un debutant complet
  ou a un enfant intelligent.
* Utilise des exemples concrets et faciles.
* Definis chaque mot technique.
* Utilise des phrases courtes.
* Pour un cours de programmation, ajoute des exemples de code simples.
* Explique chaque code avec des mots faciles.
* L'objectif est que meme un etudiant faible ou debutant puisse comprendre facilement.
* Chaque notion importante doit obligatoirement suivre le format:
  Definition simple, Explication facile, Analogie, Exemple concret,
  Pourquoi c'est important, A retenir.
* Ne fais pas un resume classique en longs paragraphes.

ATTENTION:
Ne résume pas sous forme de cours académique.
Ne fais pas de titres comme Introduction, Conclusion, I., II., III.
Respecte exactement le modèle demandé pour chaque notion.
Commence directement par:

## Introduction simple

Puis continue avec:

## Idée principale du cours
## Notion 1 : ...
## Notion 2 : ...
## Petit résumé final
## Mini-glossaire


"""

        return {
            'system': system_prompt,
            'user': user_prompt
        }

    def _call_api(self, prompt, temperature=0.1, max_tokens=8000, timeout=180):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.MODEL,
            'messages': [
                {'role': 'system', 'content': prompt['system']},
                {'role': 'user', 'content': prompt['user']}
            ],
            'temperature': temperature,
            'max_tokens': max_tokens,
            'top_p': 0.9
        }

        try:
            response = requests.post(self.API_URL, headers=headers, json=payload, timeout=timeout)

            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    usage = data.get('usage', {})
                    logger.info(f"Tokens: {usage.get('total_tokens', '?')}")
                    return {'success': True, 'content': content}
                else:
                    return {'success': False, 'error': 'Reponse API invalide: pas de contenu'}
            elif response.status_code == 401:
                return {'success': False, 'error': 'Cle API DeepSeek invalide ou expiree'}
            elif response.status_code == 429:
                return {'success': False, 'error': 'Limite de requetes DeepSeek atteinte.'}
            else:
                error_msg = response.json().get('error', {}).get('message', response.text)
                return {'success': False, 'error': f'Erreur API ({response.status_code}): {error_msg}'}

        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Timeout: la generation a pris trop de temps'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Erreur connexion DeepSeek: {str(e)}'}

    def generate_exercises(self, resume_text, course_name, difficulty='medium'):
        if not self.is_configured():
            return {'success': False, 'error': 'DeepSeek API non configuree.'}

        prompt = self._build_exercises_prompt(resume_text, course_name, difficulty=difficulty)

        try:
            response = self._call_api(prompt, temperature=0.2, max_tokens=5000, timeout=90)
            if response['success']:
                return {'success': True, 'content': response['content']}
            else:
                return {'success': False, 'error': response['error']}
        except Exception as e:
            logger.error(f"Erreur DeepSeek (exercices): {e}")
            return {'success': False, 'error': str(e)}

    def _build_exercises_prompt(self, resume_text, course_name, difficulty='medium'):
        difficulty_labels = {
            'easy': (
                'FACILE - Questions tres simples pour verifier les bases. '
                'Les questions doivent porter sur les definitions, les idees principales '
                'et les faits clairement presents dans le resume. '
                'Le langage doit etre tres simple, comme pour un etudiant debutant. '
                'Les reponses doivent etre faciles a trouver apres lecture du resume. '
                'AUCUNE question piege, AUCUNE analyse complexe, AUCUNE formulation ambigue. '
                'Les mauvaises reponses doivent etre clairement differentes de la bonne reponse. '
                'Pour les cours de programmation, les questions avec code doivent être très simples: '
                'identifier ce que fait une ligne, reconnaître une variable, comprendre une sortie évidente.'
            ),
            'medium': (
                'MOYEN - Questions de comprehension et d\'application simple. '
                'L\'etudiant doit comprendre le sens des notions, les causes, '
                'les consequences ou les relations entre les idees. '
                'Les questions peuvent demander \"pourquoi\", \"comment\" ou \"quel est le lien\", '
                'mais avec un langage simple. '
                'Les distracteurs doivent etre plausibles, mais pas trop piegeux. '
                'Chaque explication doit aider l\'etudiant a comprendre '
                'comme si on lui expliquait calmement. '
                'Pour les cours de programmation, les questions avec code peuvent demander de lire un petit code, '
                'prévoir son résultat ou choisir la bonne correction simple.'
            ),
            'hard': (
                'DIFFICILE - Questions d\'analyse et de raisonnement. '
                'Les questions peuvent presenter un petit cas, une situation '
                'ou demander de comparer deux notions proches. '
                'La difficulte doit venir du raisonnement, pas d\'un langage complique. '
                'Les distracteurs peuvent etre proches de la bonne reponse, '
                'mais ils ne doivent pas etre injustes ni ambigus. '
                'L\'explication doit detailler le raisonnement etape par etape '
                'avec des mots simples.'
                'Pour les cours de programmation, les questions avec code peuvent demander d’analyser un code court, '
                'trouver une erreur, comprendre une logique en plusieurs étapes ou comparer deux solutions.'
            ),
        }

        difficulty_text = difficulty_labels.get(difficulty, difficulty_labels['medium'])

        system_prompt = f"""Tu es un expert en creation de questions a choix multiples QCM educatives pour des cours universitaires.

Ton objectif est de creer des QCM utiles pour aider les etudiants a comprendre, reviser et memoriser facilement.

NIVEAU DE DIFFICULTE DEMANDE:
{difficulty_text}

PRINCIPE PEDAGOGIQUE IMPORTANT:
Meme si le cours est universitaire, les questions et les explications doivent etre simples a comprendre.
Explique comme si tu aidais un etudiant debutant ou un enfant intelligent.
Utilise des phrases courtes, claires et directes.
Evite le jargon complique.
Si un mot technique est necessaire, il doit etre utilise clairement et explique simplement.

REGLES STRICTES A SUIVRE:

1. Generer entre 5 et 10 questions de qualite.
2. Chaque question doit avoir exactement 4 options: A, B, C, D.
3. Une seule reponse correcte par question.
4. Adapter la difficulte au niveau demande.
5. Couvrir differents aspects importants du resume fourni.
6. NE JAMAIS inventer d'informations qui ne sont pas dans le resume.
7. Inclure une explication claire et simple pour chaque bonne reponse.
8. L'explication doit expliquer pourquoi la bonne reponse est correcte.
9. Si utile, l'explication peut aussi expliquer pourquoi les autres reponses sont fausses.
10. Les distracteurs doivent etre plausibles, mais clairement incorrects.
11. Ne pas poser de questions ambigues.
12. Ne pas utiliser de double negation ou de formulation confuse.
13. Ne pas creer des questions inutilement compliquees.
14. Les questions doivent aider l'etudiant a apprendre, pas seulement a etre piege.
15. Ne jamais utiliser des reponses comme \"Toutes les reponses sont bonnes\" ou \"Aucune reponse\".
16. INTERDICTION ABSOLUE: ne jamais utiliser \"Concept A\", \"Concept B\", \"Option A\",
    \"Option B\" ou tout placeholder generique.
17. Chaque option doit etre un texte reel, precis et pertinent base sur le contenu du resume.
18. Pour les cours de programmation, certaines questions peuvent contenir un extrait de code si cela aide à tester la compréhension.
19. Ne mets jamais les extraits de code directement dans le texte de la question avec des blocs Markdown.
20. Si une question contient du code, utilise les champs "code_language" et "code_block".
21. Si une question ne contient pas de code, mets "code_language": null et "code_block": null.
22. Le code doit être court, simple et basé uniquement sur le résumé.

STYLE DES QUESTIONS:

* Questions courtes et faciles a lire.
* Vocabulaire simple.
* Une seule idee principale par question.
* Options de longueur raisonnable.
* Pas d'options trop longues.
* Pas de formulation volontairement trompeuse.
* Meme les questions difficiles doivent rester claires.

STYLE DES EXPLICATIONS:

* Expliquer simplement.
* Utiliser des exemples courts si cela aide.
* Montrer le raisonnement etape par etape pour les questions moyennes ou difficiles.
* Ne pas etre trop academique.
* L'explication doit vraiment aider l'etudiant a comprendre la notion.
* L'explication doit etre utile meme si l'etudiant a choisi la mauvaise reponse.


IMPORTANT POUR LE CODE:
- Le champ "code_block" doit contenir uniquement le code brut.
- Ne pas utiliser ```python dans le JSON.
- Utilise \\n pour les retours à la ligne dans le code.
- Exemple:
  "code_block": "x = 5\\nprint(x + 2)"


FORMAT DE SORTIE OBLIGATOIRE:

Tu dois retourner uniquement un JSON valide.
Aucun texte avant.
Aucun texte apres.
Aucun bloc Markdown.
Aucun commentaire.
Aucune virgule finale.
Utilise uniquement des guillemets doubles pour les cles et les valeurs JSON.

Le JSON doit être un tableau JSON valide.
La valeur de "correct_answer" doit être uniquement "A", "B", "C" ou "D".
Chaque objet doit contenir exactement les clés suivantes:
"question", "code_language", "code_block", "options", "correct_answer", "explanation".
Si la question ne contient pas de code:
- "code_language": null
- "code_block": null

Si la question contient du code:
- "code_language": "python" ou le langage adapté
- "code_block": "code brut sans Markdown"

Ne mets jamais ```python ou ```json dans le JSON.
Ne retourne jamais un objet contenant "questions".
Ne retourne jamais du Markdown.
Ne retourne jamais de texte avant ou après le JSON.


FORMAT JSON ATTENDU:

[
{{
"question": "Texte clair et simple de la question ?",
 "code_language": null,
    "code_block": null,
"options": {{
"A": "Texte reel de l'option A base sur le resume",
"B": "Texte reel de l'option B base sur le resume",
"C": "Texte reel de l'option C base sur le resume",
"D": "Texte reel de l'option D base sur le resume"
}},
"correct_answer": "A",
"explanation": "Explication simple de pourquoi cette reponse est correcte."
}}
]"""

        user_prompt = f"""Voici un resume de cours pour lequel tu dois generer des QCM:

COURS: {course_name}
NIVEAU: {difficulty_text}

RESUME:
{resume_text}

---

Genere maintenant des QCM en francais a partir de ce resume.

Tres important:

* Les questions doivent etre simples a comprendre.
* Meme les questions difficiles doivent utiliser un langage clair.
* Les explications doivent etre pedagogiques, comme si tu expliquais a un etudiant debutant.
* Ne cree aucune information qui n'est pas presente dans le resume.
* Ne pose pas de question ambigue.
* Respecte strictement le format JSON demande.
* Retourne uniquement le JSON, sans texte autour."""

        return {
            'system': system_prompt,
            'user': user_prompt
        }

    def translate_summary(self, text, target_language='fr'):
        if not self.is_configured():
            return {'success': False, 'error': 'Service non configure'}

        system_prompt = (
            'Tu es un traducteur academique expert.\n'
            'Traduis le texte suivant en ' + target_language + '.\n\n'
            'REGLES:\n'
            '1. Conserve le sens exact et le formatage Markdown original.\n'
            '2. Traduction naturelle, fluide et humaine.\n'
            '3. Preserve les blocs de code, formules LaTeX, tableaux, citations.'
        )

        user_prompt = 'Texte a traduire:\n\n' + text

        try:
            response = self._call_api({'system': system_prompt, 'user': user_prompt}, temperature=0.3)
            if response['success']:
                return {'success': True, 'content': self._clean_text(response['content'])}
            return response
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def reformulate_summary(self, text):
        if not self.is_configured():
            return {'success': False, 'error': 'Service non configure'}

        system_prompt = (
            'Tu es un expert en pedagogie universitaire.\n'
            'Reformule le texte pour le rendre plus fluide, clair et engageant.\n\n'
            'REGLES:\n'
            '1. Ne perds aucune information essentielle.\n'
            '2. Ameliore les transitions entre les idees.\n'
            '3. PRESERVE le formatage Markdown (code, LaTeX, tableaux, listes).'
        )

        user_prompt = 'Texte a reformuler:\n\n' + text

        try:
            response = self._call_api({'system': system_prompt, 'user': user_prompt}, temperature=0.4)
            if response['success']:
                return {'success': True, 'content': self._clean_text(response['content'])}
            return response
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def simplify_summary(self, text):
        if not self.is_configured():
            return {'success': False, 'error': 'Service non configure'}

        system_prompt = (
            'Tu es un vulgarisateur scientifique expert.\n'
            'Simplifie les concepts complexes sans sacrifier la precision.\n\n'
            'REGLES:\n'
            '1. Explique les termes techniques.\n'
            '2. Utilise des analogies si necessaire.\n'
            '3. PRESERVE le formatage Markdown (code, LaTeX, tableaux, listes).'
        )

        user_prompt = 'Texte a simplifier:\n\n' + text

        try:
            response = self._call_api({'system': system_prompt, 'user': user_prompt}, temperature=0.4)
            if response['success']:
                return {'success': True, 'content': self._clean_text(response['content'])}
            return response
        except Exception as e:
            return {'success': False, 'error': str(e)}


deepseek_service = DeepSeekService()
