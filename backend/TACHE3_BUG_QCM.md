
1.### Problème actuel

La structure des exercices a été corrigée, mais un seul exercice est encore créé pour un résumé.

Si l’utilisateur sélectionne plusieurs niveaux, par exemple **Facile, Moyen et Difficile**, l’application conserve uniquement le premier niveau sélectionné. Les questionnaires sont donc eux aussi rattachés au mauvais exercice et se mélangent.

### Comportement attendu

Pour chaque combinaison :

**Utilisateur + Résumé + Niveau**

il doit exister **un exercice distinct**.

Exemple :

* Résumé X + Facile → Exercice Facile
* Résumé X + Moyen → Exercice Moyen
* Résumé X + Difficile → Exercice Difficile

### Règle de création

Lorsqu’un utilisateur sélectionne un niveau :

1. Vérifier si **son exercice pour ce résumé et ce niveau existe déjà**.
2. S’il existe → **ne rien régénérer** et réutiliser cet exercice.
3. S’il n’existe pas → **créer un nouvel exercice pour ce niveau** et générer ses propres questionnaires.
4. Les questionnaires doivent être exclusivement attachés à cet exercice.

La régénération doit donc être bloquée uniquement pour **le même utilisateur + même résumé + même niveau**.

En revanche, si l’utilisateur change de niveau et que cet exercice n’existe pas encore, **un nouvel exercice doit obligatoirement être créé**.

### Exemple

L’utilisateur génère d’abord :

**Résumé X + Facile**
→ création de l’Exercice Facile
→ questionnaires Faciles.

Puis :

**Résumé X + Moyen**
→ l’Exercice Moyen n’existe pas
→ création d’un nouvel Exercice Moyen
→ questionnaires Moyens.

Puis :

**Résumé X + Difficile**
→ création d’un nouvel Exercice Difficile
→ questionnaires Difficiles.

Il ne faut jamais réutiliser l’Exercice Facile pour le Moyen ou le Difficile.

### Vérification importante

Vérifier particulièrement la logique qui détermine l’exercice à récupérer avant la génération. Actuellement, elle semble identifier uniquement le résumé/utilisateur et ignore encore correctement le **niveau de difficulté**, ce qui explique pourquoi le premier exercice est conservé et que les questionnaires se retrouvent mélangés.

### Tentatives

Les tentatives doivent rester liées à **l’exercice correspondant au niveau sélectionné**.

Exemple :

**Tentative Difficile → Exercice Difficile → questionnaires Difficiles uniquement.**

### Interface

Supprimer le bouton **« Régénérer »** dans l’écran des tentatives.

Il doit rester uniquement le bouton **« Retour »**.

### Objectif final

La règle doit être strictement :

**Utilisateur + Résumé + Niveau = un exercice unique**

Puis :

**Exercice → ses questionnaires → ses tentatives**

Aucune donnée d’un niveau ne doit être écrasée, réutilisée ou mélangée avec celle d’un autre niveau.




2### Tâche — Étendre la détection des contenus à mettre en évidence

La logique actuelle fonctionne déjà correctement pour les contenus de programmation :

* `code_language`
* `code_block`

Ces deux valeurs sont renvoyées par les générations DeepSeek (résumé, traduction, QCM/exercices) et permettent à Flutter d’identifier certains contenus et d’appliquer un affichage spécifique, notamment la zone grisée.

**Ne pas casser cette logique existante.**

### Nouveau besoin

Je veux étendre cette logique afin que la zone d’affichage spécifique ne soit pas réservée uniquement au code de programmation.

Elle doit également pouvoir être utilisée lorsqu’un contenu généré contient :

* une **expression mathématique** ;
* une **formule mathématique** ;
* une **expression ou notation particulière** qui nécessite un affichage distinct ;
* du **code de programmation**, comme actuellement.

Exemples :

> Que signifie l’expression `E = mc²` ?

ou

> `f(x) = ax² + bx + c`

Ces expressions doivent pouvoir être identifiées et affichées dans la zone prévue côté Flutter, exactement comme le code l’est actuellement.

### À faire avant toute modification

Analyser précisément la logique actuelle :

1. Où `code_language` et `code_block` sont générés par DeepSeek.
2. Dans quels prompts ces champs sont demandés.
3. Comment leurs valeurs sont enregistrées en base.
4. Quelle condition Flutter utilise pour décider d’afficher la zone grisée.
5. Vérifier si la présence de `code_language`, de `code_block` ou des deux déclenche cet affichage.
6. Identifier la meilleure manière d’étendre cette logique sans modifier le comportement actuel.

### Modification souhaitée

Adapter les prompts DeepSeek afin que la réponse puisse également indiquer la nature du contenu lorsqu’il s’agit d’une :

* formule mathématique ;
* expression mathématique ;
* notation particulière ;
* expression nécessitant un rendu spécifique ;
* programmation/code.

Il faut conserver `code_language` et `code_block` si leur logique actuelle peut être réutilisée, ou proposer une extension propre si ces champs ne sont pas adaptés à tous les nouveaux cas.

**Important : ne pas modifier arbitrairement le frontend Flutter avant d’avoir compris la condition actuelle qui déclenche la zone grisée.**

L’objectif est que DeepSeek fournisse une information suffisamment fiable pour que Flutter sache :

**contenu normal → affichage normal**

**code / formule / expression particulière → affichage spécifique (zone grisée)**

### Attention

Le système actuel fonctionne déjà presque correctement. Il faut donc privilégier une **modification minimale et compatible avec l’existant**, sans casser :

* la génération des résumés ;
* la traduction ;
* la génération des QCM/exercices ;
* les contenus de programmation existants ;
* `code_language` ;
* `code_block` ;
* l’affichage Flutter actuel.

Avant de coder, expliquer clairement **où se trouve actuellement la logique et comment elle fonctionne**, puis proposer la modification nécessaire.

