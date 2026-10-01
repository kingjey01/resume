## ONBOARDING CP — TRANSACTION ATOMIQUE ET PRÉVENTION DES DOUBLONS

Analyser d'abord le code actuel de l'onboarding CP afin de vérifier si un mécanisme transactionnel ou de rollback existe déjà. **Ne pas recréer une logique qui existe déjà.**

### Problème

Actuellement, l'onboarding CP comporte plusieurs étapes :

**Création du cours,Création du professeur,Félicitations (Association cours/professeur )/ fin de l'onboarding**

Si le CP crée un cours ou un professeur puis quitte l'onboarding avant d'atteindre l'étape finale, les données sont déjà enregistrées.

Lorsqu'il reprend l'onboarding plus tard, il peut donc recréer le même cours/professeur et provoquer des doublons.

### Correction demandée

Rendre l'ensemble de l'opération d'onboarding CP **atomique**.

La création :

* du cours ;
* du professeur ;
* de l'association `Dispense`

doit être considérée comme **une seule opération métier**.

Tant que le CP n'a pas atteint et validé l'étape finale de l'onboarding (écran de félicitations), l'opération ne doit pas être considérée comme terminée.

Si l'utilisateur quitte ou abandonne l'onboarding avant cette étape :

* annuler/rollback les créations effectuées pendant cet onboarding ;
* ne conserver aucun cours, professeur ou `Dispense` créé partiellement ;
* permettre à l'utilisateur de reprendre l'onboarding proprement plus tard.

Lorsque toutes les étapes sont correctement terminées et que l'utilisateur atteint l'étape finale :

* valider définitivement le cours ;
* valider définitivement le professeur ;
* l'association `Dispense` est effectuée.

Utiliser une véritable transaction backend (`transaction.atomic` ou mécanisme équivalent) afin de garantir qu'il n'existe jamais de création partielle.

**Important :** ne pas supprimer des données préexistantes appartenant à l'utilisateur. Le rollback doit concerner uniquement les données créées dans le cadre de la tentative d'onboarding en cours.

Objectif final :

**Onboarding terminé → tout est enregistré.**

**Onboarding abandonné/incomplet → rien de cette tentative n'est conservé.**

Cela doit empêcher la création de doublons lors de la reprise de l'onboarding.
