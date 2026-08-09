Corriger la génération des QCM dans `personalized_exercises_generator` et `personalized_exercise_view`.

Le générateur produit actuellement des questions trop génériques, basées sur des mots-clés ou des notions abstraites, au lieu de poser de vraies questions à partir du contenu réel des résumés.

Avant toute modification, analyser et comparer :

* `exercises_generator`
* `exercise_view`
* `personalized_exercise_generator`
* `personalized_exercise_view`

Identifier précisément pourquoi la logique utilisée dans la exercices_generator  produit des questions pertinentes à partir du contenu des résumés, puis appliquer cette même logique au générateur personalisé sans casser son fonctionnement actuel.

### Règles obligatoires

Les QCM doivent être générés **uniquement à partir des informations réellement présentes dans les résumés fournis**.

Ne jamais inventer de concepts, de notions ou de contenu absent du résumé.

Interdire les questions artificielles du type :

* « Quel concept A est correct ? »
* « Que signifie le concept B ? »
* « Parmi les concepts A, B, C et D... »

si ces concepts ne sont pas explicitement présents dans le résumé.

Les propositions A, B, C et D doivent être de **véritables réponses liées au contenu du résumé**, et non des placeholders ou des notions génériques comme: A) concept A , B) Concept B

Pour les matières techniques et les algorithmes, les questions doivent tester la compréhension réelle du contenu : fonctionnement, résultat d'un code, logique d'un algorithme, comportement d'une fonction, application d'une formule, etc., lorsque ces éléments sont présents dans le résumé.

Le générateur doit donc d'abord exploiter le contenu réel du résumé, puis construire les questions et propositions à partir de ce contenu.

Ne pas modifier inutilement l'architecture existante. Réutiliser la logique déjà validée dans le système `personalized_*` et l'adapter au générateur standard.
