## OBJECTIF

Le système fonctionne actuellement correctement : endpoints, traitements, réponses API et intégration frontend sont déjà opérationnels.

Tu dois intervenir **EXCLUSIVEMENT dans les fichiers backend responsables de la génération des exercices personnalisés et du filtrage des questions/réponses générées**.

### RÈGLE ABSOLUE — AUCUNE RÉGRESSION

* Ne supprime aucune fonctionnalité existante.
* Ne modifie aucun endpoint existant.
* Ne modifie aucune URL.
* Ne modifie aucune structure de réponse API.
* Ne modifie aucun nom de champ retourné.
* Ne rajoute aucune variable dans la réponse API.
* Ne change pas le format attendu par le frontend.
* Ne modifie pas les modèles de données sauf si cela est strictement indispensable, ce qui n'est normalement pas nécessaire.
* Ne touche à aucun fichier frontend.
* Ne touche à aucun autre module backend.
* Ne modifie pas les fonctionnalités de génération de résumé, transcription, cours, professeurs, etc.
* Ne remplace pas la logique actuelle : **améliore-la sans casser ce qui fonctionne déjà.**

La valeur de retour de la génération des exercices doit rester **strictement identique à l'existant**.

L'objectif est uniquement d'améliorer :

1. le prompt envoyé au modèle IA pour générer les exercices personnalisés ;
2. le filtrage/validation des exercices générés ;
3. la distribution des bonnes réponses ;
4. la qualité et la difficulté réelle des questions selon le niveau.

---

# 1. DISTRIBUTION DES BONNES RÉPONSES

Le système actuel présente un défaut critique : les bonnes réponses sont parfois regroupées.

Exemple interdit :

* Question 1 → A
* Question 2 → A
* Question 3 → A
* Question 4 → B
* Question 5 → B
* Question 6 → B

Cette organisation permet à l'utilisateur de deviner les réponses sans connaître le contenu.

### NOUVELLE RÈGLE STRICTE

Les bonnes réponses doivent être **réparties de manière pseudo-aléatoire et équilibrée** entre les différentes positions disponibles.

Exemple acceptable :

* Question 1 → A
* Question 2 → C
* Question 3 → B
* Question 4 → D
* Question 5 → B
* Question 6 → A
* Question 7 → D
* Question 8 → C

Il faut absolument éviter :

* trois mêmes réponses consécutives ;
* plusieurs mêmes réponses regroupées ;
* une longue série A, puis une longue série B, etc. ;
* un schéma prévisible ;
* une position de bonne réponse systématiquement privilégiée.

### CONTRAINTE DE FILTRAGE

Après génération par l'IA, le backend doit contrôler la séquence des bonnes réponses.

Si la distribution est trop répétitive ou prévisible :

1. ne pas retourner immédiatement les exercices ;
2. corriger/réorganiser la distribution si cela peut être fait sans modifier le contenu ;
3. sinon régénérer/retraiter les exercices concernés ;
4. effectuer une nouvelle validation avant le retour final.

Le résultat final doit présenter une distribution naturelle, variée et non prévisible.

**Important :** cette correction ne doit jamais modifier la structure de retour existante.

---

# 2. QUESTIONS BASÉES EXCLUSIVEMENT SUR LE RÉSUMÉ

Les exercices personnalisés doivent être construits à partir du **contenu réel du résumé fourni**.

L'IA ne doit pas produire des questions génériques simplement parce qu'elle connaît le domaine ou le sujet général.

La question doit tester une information, une relation, une explication, une distinction, une conséquence, une procédure ou un raisonnement qui existe réellement dans le résumé.

### QUESTIONS INTERDITES

Éliminer les formulations génériques ou artificielles telles que :

* « D'après le résumé, quelle phrase... »
* « D'après le résumé, que signifie... »
* « D'après le résumé, quelle phrase parle de... »
* « Selon le résumé, quelle phrase correspond à... »
* « D'après le résultat, quelle phrase... »
* « Quelle phrase du résumé parle de... »
* « Quelle phrase décrit l'objet... »
* « Quelle phrase correspond au schéma... »
* « Selon le contenu, quelle phrase... »
* « D'après ce qui est présenté, quelle affirmation... » lorsque cette formulation ne teste aucune connaissance précise.

Éviter également les questions qui demandent simplement à l'utilisateur de reconnaître ou mémoriser une phrase exacte du résumé.

### PRINCIPE

Ne pas demander :

> « Quelle phrase du résumé décrit X ? »

Mais construire une vraie question de compréhension, par exemple :

> « Quel est le rôle de X dans le processus décrit dans le résumé ? »

ou :

> « Quelle conséquence se produit lorsque X est appliqué dans le processus présenté ? »

ou :

> « Quelle différence le résumé établit-il entre X et Y ? »

La formulation exacte dépend évidemment du contenu réel du résumé.

---

# 3. LE NIVEAU DE DIFFICULTÉ DOIT ÊTRE RÉEL

Le niveau choisi par l'utilisateur doit avoir une conséquence réelle sur la construction des questions.

## FACILE

Le niveau facile doit principalement vérifier :

* les notions essentielles ;
* les définitions ;
* l'identification d'un concept ;
* les informations explicitement présentes ;
* les relations simples entre les éléments du résumé.

Les questions doivent rester accessibles sans être triviales.

## MOYEN

Le niveau moyen doit demander davantage de compréhension.

Utiliser notamment :

* comparaison ;
* distinction entre deux concepts ;
* relation entre plusieurs informations du résumé ;
* cause et conséquence ;
* application d'une règle présentée ;
* interprétation d'une situation ;
* choix entre plusieurs concepts proches ;
* raisonnement à partir de plusieurs éléments du résumé.

Une question moyenne ne doit pas être simplement une question facile reformulée.

## DIFFICILE

Le niveau difficile doit réellement nécessiter du raisonnement.

Les questions peuvent demander :

* analyse ;
* déduction ;
* raisonnement multi-étapes ;
* application d'un concept à une situation nouvelle ;
* identification d'une conséquence non explicitement formulée mais déductible du résumé ;
* comparaison de plusieurs concepts ;
* résolution d'un problème basé sur les connaissances du résumé ;
* distinction entre des propositions très proches mais dont une seule respecte précisément le contenu du résumé.

Le niveau difficile doit donc être **plus exigeant cognitivement** que le niveau moyen, lui-même plus exigeant que le niveau facile.

---

# 4. SOURCE UNIQUE DES CONNAISSANCES

Pour les exercices personnalisés :

**LE RÉSUMÉ EST LA SOURCE DE VÉRITÉ.**

L'IA ne doit pas inventer des informations extérieures au résumé pour construire les réponses.

Elle peut utiliser ses capacités de raisonnement uniquement pour :

* reformuler ;
* comparer ;
* déduire ;
* construire des situations ;
* créer des distracteurs plausibles ;
* augmenter la difficulté.

Mais les connaissances nécessaires pour résoudre la question doivent provenir du résumé.

### INTERDICTION

Ne pas générer une question uniquement parce qu'elle est généralement pertinente dans le domaine.

Chaque exercice doit pouvoir être justifié par une ou plusieurs informations concrètes présentes dans le résumé.

---

# 5. DISTRACTEURS

Les mauvaises réponses doivent être plausibles et liées au contenu.

Éviter les distracteurs :

* absurdes ;
* manifestement faux ;
* hors sujet ;
* beaucoup plus longs ou beaucoup plus courts que la bonne réponse uniquement pour la rendre identifiable ;
* contenant des formulations qui donnent involontairement la réponse ;
* ne correspondant pas au niveau de difficulté demandé.

Pour les niveaux moyen et difficile, les distracteurs doivent être suffisamment proches conceptuellement pour obliger l'utilisateur à comprendre le contenu.

---

# 6. FILTRAGE OBLIGATOIRE APRÈS GÉNÉRATION

Ne fais pas confiance aveuglément à la sortie du modèle IA.

Après réception de la génération, appliquer un filtrage backend.

Chaque exercice doit être contrôlé avant d'être retourné.

Vérifier au minimum :

### A. Pertinence

La question doit être directement liée au résumé.

### B. Spécificité

La question doit porter sur une connaissance identifiable du résumé.

### C. Niveau

La complexité doit correspondre au niveau demandé.

### D. Absence de formulation générique

Rejeter les questions utilisant des structures génériques du type :

* « D'après le résumé... »
* « Selon le résumé... »
* « Quelle phrase... »
* « Quelle phrase du résumé... »
* « Que signifie cette phrase... »

lorsque ces formulations ne produisent pas une vraie question pédagogique.

### E. Répétition

Éviter plusieurs questions testant exactement la même information sous une formulation légèrement différente.

### F. Réponses

Vérifier qu'une seule réponse est correcte.

### G. Distribution

Vérifier que les positions des bonnes réponses ne forment pas une séquence prévisible.

---

# 7. RÉGÉNÉRATION SI LA SORTIE EST MAUVAISE

Si une question échoue aux contrôles :

* ne pas la retourner ;
* ne pas dégrader les autres questions pour conserver artificiellement le nombre demandé ;
* tenter de régénérer/remplacer uniquement les éléments invalides lorsque la logique actuelle le permet ;
* conserver toutes les questions déjà valides.

Si la génération entière présente un problème de qualité, appliquer le mécanisme de retraitement déjà disponible plutôt que modifier l'architecture existante.

---

# 8. PRÉSERVER LE CONTRAT EXISTANT

C'est une contrainte critique.

Le frontend fonctionne déjà avec le format actuel.

Par conséquent :

**NE PAS MODIFIER LE CONTRAT API.**

La correction doit être invisible pour le frontend :

```text
Même endpoint
        ↓
Même paramètres
        ↓
Même traitement global
        ↓
Prompt amélioré
        ↓
Filtrage/validation amélioré
        ↓
Même structure de réponse
        ↓
Frontend inchangé
```

Aucune nouvelle propriété ne doit être ajoutée dans la réponse.

Aucune propriété existante ne doit être renommée ou supprimée.

---

# 9. ORDRE DE PRIORITÉ

Lors de l'implémentation, respecter cet ordre :

1. Préserver le fonctionnement actuel.
2. Préserver le contrat API.
3. Préserver le frontend.
4. Améliorer le prompt de génération.
5. Ajouter les règles strictes de qualité.
6. Filtrer les questions génériques.
7. Contrôler le niveau de difficulté.
8. Contrôler la distribution des bonnes réponses.
9. Régénérer uniquement les éléments invalides lorsque nécessaire.

---

# 10. RÈGLE FINALE

Ne cherche pas à réécrire ou refactoriser inutilement le système.

**Le système actuel fonctionne.**

Il faut uniquement le faire progresser sur la qualité des exercices personnalisés.

Toute modification qui n'est pas directement liée à :

* la génération des exercices personnalisés ;
* leur prompt ;
* leur validation ;
* leur filtrage ;
* leur niveau de difficulté ;
* la distribution des bonnes réponses ;

est interdite.

Avant de terminer, vérifie que :

* les endpoints sont inchangés ;
* les paramètres sont inchangés ;
* les réponses API sont inchangées ;
* le frontend n'a pas été modifié ;
* aucune fonctionnalité existante n'a régressé ;
* les questions sont réellement issues du résumé ;
* les questions génériques sont filtrées ;
* les niveaux moyen et difficile sont réellement plus exigeants ;
* les bonnes réponses sont correctement réparties et non prévisibles.
