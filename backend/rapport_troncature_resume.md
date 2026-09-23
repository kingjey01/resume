# Rapport — Résumés IA tronqués (Tâche 29, point 2)

Date : 21/09/2026. Mesures faites avec `diagnostic_truncature_resume.py`
(audio de test `IPP.amr`), sur la base de développement.

## Conclusion

La troncature vient de **l'étape de génération DeepSeek**, pas de la base de
données, ni des serializers, ni de Flutter.

**Cause précise** : le modèle `deepseek-v4-flash` est un modèle qui **raisonne**
avant de rédiger. Son raisonnement (`reasoning_content`) n'est pas affiché mais
**consomme le même plafond `max_tokens` que le résumé**. La longueur du
raisonnement varie fortement d'un appel à l'autre : pour le même prompt, on a
mesuré de 3 660 à 15 873 caractères de raisonnement. Quand le raisonnement est
long, le budget de 8 000 tokens est épuisé avant la fin du résumé, l'API renvoie
`finish_reason = "length"` — et le résumé coupé était enregistré comme s'il
était complet, **sans aucun signalement**.

C'est ce qui explique le caractère **aléatoire** du symptôme (« parfois »
incomplets) : il dépend du hasard du raisonnement, pas du contenu du cours.

### Reproduit en direct

Sur l'audio de test `IPP.amr` (13 min 36 s), avec le prompt de production :

| Appel | finish_reason | raisonnement | résumé | état |
|---|---|---|---|---|
| prompt de production, audio réel, budget 8 000 | `length` | 15 873 car. | 9 513 car. | **COUPÉ** |
| robustesse, essai 1, budget 8 000 | `length` | — | — | **COUPÉ** (8000/8000 tokens) |
| robustesse, essai 1, relance à 16 000 | `stop` | — | 10 220 car. | complet ✅ |
| robustesse, essais 2 et 3, budget 8 000 | `stop` | — | 14 394 / 13 038 car. | complets (pas de coupure) |

Les essais 2 et 3 illustrent le caractère aléatoire : le même prompt, au même
budget de 8 000, a produit tantôt un résumé complet, tantôt un résumé coupé.

## Étapes vérifiées, dans l'ordre

| # | Étape | Verdict |
|---|---|---|
| 1 | Audio → transcription Deepgram | **Dégradée** : mauvais type MIME pour les `.amr` (voir ci-dessous) |
| 2 | Prompt envoyé à DeepSeek | Transcription complète envoyée, aucun élagage |
| 3 | Réponse brute DeepSeek | **COUPÉE** — `finish_reason = "length"` |
| 4 | `_clean_text()` | Neutre : nombre de mots identique avant/après |
| 5 | Base de données | Neutre : écriture + relecture identiques (`TextField`) |
| 6 | Serializer / API | Neutre pour le CP (`/summaries/validation/` renvoie le texte brut) |
| 7 | Flutter | Aucune troncature hors aperçu payant volontaire |

Détail des vérifications :

- **Base de données** — `Summary.texte_resume` est un `TextField` ; SQLite en dev
  et PostgreSQL en production n'imposent aucune limite. Aller-retour vérifié :
  9 513 caractères écrits, 9 513 relus.
- **`_clean_text()`** — normalise les espaces (espaces multiples, sauts de ligne)
  mais ne perd **aucun mot** : 1 325 → 1 325 mots, 2 298 → 2 298 mots.
- **Serializers** — `SummarySerializer` tronque à 50 / 100 / 150 caractères pour
  les non-acheteurs. Ce sont des **aperçus payants volontaires**. Le CP reçoit le
  texte complet : vérifié route par route avec un compte CP sur un résumé de
  13 599 caractères.
- **Flutter** — `summary_details_screen.dart` n'affiche `substring(0, 150)` que
  dans la branche verrouillée, cohérente avec l'aperçu backend.

## Défauts corrigés

1. **Troncature silencieuse** (`deepseek_service.py`) — `_call_api()` ignorait
   `finish_reason`. Ajout de la détection, d'un log explicite, et d'un **nouvel
   essai avec un budget plus large** (8 000 → 16 000 → 24 000) uniquement quand
   l'API signale elle-même la coupure. Le coût normal reste inchangé : le premier
   essai reste à 8 000.

2. **Type MIME des fichiers `.amr`** (`deepgram_service.py`) — la table MIME
   ignorait `.amr`, `.3gp`, `.opus`, `.aac`… et envoyait `audio/wav` pour un
   fichier AMR. Mesuré : **2 800 mots transcrits au lieu de 2 854** sur
   `IPP.amr`, soit ~2 % de contenu perdu avant même le résumé. Table complétée
   + repli sur `mimetypes` de la bibliothèque standard avec avertissement.

3. **`SummarySerializer` sans `context`** (`views.py:365`) — dans
   `generate_summary_from_audio()`, le serializer était instancié sans
   `context={'request': request}`. `to_representation()` y voyait un utilisateur
   non authentifié et tronquait `texte_resume` à **50 caractères**, avec
   `is_purchased` toujours à `false`. Corrigé.

## Point 3 — Génération de QCM : prévention

La génération de QCM (`generate_exercises`) utilise le même modèle raisonnant
avec un plafond fixe de 5 000 tokens. Le mode de défaillance est **différent et
plus sournois** que pour les résumés : une réponse coupée donne un **JSON
invalide**, le parsing échoue, et les deux générateurs
(`exercise_generator.py`, `personalized_exercise_generator.py`) retombent
**silencieusement** sur des questions génériques locales (`fallback_local`).
L'utilisateur reçoit alors un QCM sans rapport avec son résumé, et les logs
n'indiquaient qu'un vague « parsing JSON échoué ».

**Traitement appliqué** (même mécanisme que les résumés) :

- Paliers de budget dédiés `EXERCISES_TOKEN_BUDGETS = (5000, 10000, 16000)`,
  utilisés via un helper partagé `_call_api_jusqua_complet()`.
- Le repli local distingue désormais explicitement le cas « réponse **coupée** »
  du reste, au lieu de le confondre avec un JSON simplement mal formé.

**Mesure honnête de l'ampleur du risque** : avec un résumé de 35 820 caractères,
**8 appels sur 8** au plafond d'origine de 5 000 tokens se sont terminés
normalement (`finish_reason='stop'`, JSON valide, 8 à 10 questions). **Aucune
coupure naturelle n'a été reproduite** sur ce chemin.

L'explication est structurelle : le prompt QCM borne la sortie (5 à 10 questions
à 4 options, soit ~4 500 à 5 800 caractères), alors que le prompt de résumé
demande explicitement d'être complet et peut produire 17 000 caractères. Le
QCM a donc une marge bien plus large.

En revanche, le mécanisme de secours **fonctionne** : avec un premier palier
forcé à 64 tokens, la coupure est détectée, l'escalade se déclenche et produit
**7 questions valides** au lieu d'un repli sur du QCM générique.

Autrement dit : la protection est en place et vérifiée, mais elle n'a **pas**
corrigé un bug observé — elle supprime un risque non reproduit et, surtout, rend
désormais visible dans les logs une coupure qui passait inaperçue.

## Point signalé, NON modifié

**`IPP.amr` s'arrête en pleine phrase** — le fichier de test lui-même se termine
sur « et là tu te poses, ». Deepgram transcrit jusqu'à 807,07 s sur 816,32 s,
avec les deux types MIME. Ce n'est pas une troncature de Deepgram :
l'enregistrement est coupé. Un résumé de ce fichier sera donc forcément
« incomplet » — c'est normal et sans lien avec le bug corrigé.

## Outil de diagnostic conservé

`backend/diagnostic_truncature_resume.py` — suit toute la chaîne et vérifie
l'absence de perte à chaque étape. Lecture seule, transaction annulée.

```
cd backend && ./.venv/Scripts/python.exe diagnostic_truncature_resume.py
```

## Tests

`backend/courses/test_delete_summary.py` — 7 tests (voir point 1 de la tâche).
Suite complète : `./.venv/Scripts/python.exe manage.py test courses` → **16 tests OK**.
