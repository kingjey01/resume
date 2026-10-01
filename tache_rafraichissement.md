## Objectif général

Analyser et corriger les trois problèmes ci-dessous dans l'application, en conservant l'architecture, le design et les comportements métiers existants. Ne pas créer de logique parallèle inutile : identifier la cause réelle du problème et corriger la gestion d'état, le rafraîchissement et les filtres concernés.

### 1. Empêcher la réapparition de l'onboarding CP après sa finalisation

Il existe actuellement un problème intermittent avec l'onboarding des CP.

Lorsqu'un CP termine toutes les tâches de l'onboarding et finalise correctement le processus, les données sont bien enregistrées. Cependant, **dans certains cas**, lorsqu'il quitte la page, va dans le menu ou dans une autre section puis revient en arrière, la page d'onboarding apparaît de nouveau alors qu'elle a déjà été finalisée.

#### À vérifier

* Vérifier précisément comment l'état de finalisation de l'onboarding est enregistré côté backend et côté frontend.
* Vérifier que l'application récupère bien cet état après la finalisation.
* Vérifier qu'une fois l'onboarding terminé, l'état est immédiatement mis à jour dans l'état global de l'application.
* Vérifier les conditions de navigation qui peuvent provoquer la réouverture de la page d'onboarding.
* Vérifier qu'il n'existe pas de cache, ancien état local ou état frontend obsolète permettant à la page de réapparaître.
* Vérifier également le comportement lorsqu'un utilisateur revient en arrière avec le bouton/navigation système.

#### Comportement attendu

Dès que le CP clique sur **Finaliser** :

1. Toutes les données sont enregistrées.
3. L'état frontend/global est actualisé immédiatement.
4. L'application effectue le rafraîchissement nécessaire.
5. Si le CP click sur le bouton aller dans acceuil , au menu ou navigue ailleurs puis revient en arrière, **l'onboarding ne doit plus jamais être affiché**.
6. La page d'onboarding doit être protégée par une vérification fiable du statut de finalisation.

Mettre donc une **barrière métier définitive** :

> Si l'onboarding CP est déjà finalisé, la route/page d'onboarding ne doit plus être accessible comme étape à effectuer, même si une ancienne donnée frontend ou un ancien état de navigation existe.

L'objectif est d'éliminer totalement le risque de doublon ou de réapparition de l'onboarding après finalisation.

---

### 2. Effectuer un véritable rafraîchissement global lorsque le statut utilisateur change

Deuxième problème : lorsqu'une **demande pour devenir CP est acceptée**, certaines parties de l'application sont correctement actualisées, mais d'autres ne le sont pas.

Actuellement, après acceptation de la demande :

* le cadre concernant la demande CP est correctement actualisé ;
* mais la barre de navigation n'est pas toujours actualisée ;
* certaines options restent à 4 au lieu de 5 ;
* les éléments liés à la validation du statut CP peuvent ne pas apparaître ;
* le bouton/icône **+** permettant certaines actions CP peut ne pas apparaître immédiatement.

L'utilisateur doit parfois quitter complètement l'application, la mettre en arrière-plan ou se déconnecter/reconnecter pour que son nouveau statut CP soit correctement pris en compte.

#### À vérifier

Identifier toutes les données dépendantes du statut utilisateur :

* rôle/statut CP ;
* permissions ;
* éléments de navigation ;
* nombre d'onglets ;
* bouton **+** ;
* fonctionnalités réservées aux CP ;
* validations ;
* informations utilisateur récupérées depuis le backend ;
* état global utilisé par les différents écrans.

Vérifier également si certains widgets utilisent encore une ancienne instance de l'utilisateur ou un ancien état du profil.

#### Comportement attendu

L'icône/bouton de **rafraîchissement** de l'application doit effectuer un **rafraîchissement global réel de l'état de l'application**, et pas uniquement recharger les données de la page actuellement affichée.

Lorsque l'utilisateur clique sur Actualiser depuis l'accueil :

1. Recharger les informations utilisateur depuis le backend.
2. Recharger son rôle/statut et ses permissions.
3. Mettre à jour l'état global de l'application.
4. Recalculer les éléments de navigation.
5. Recalculer les fonctionnalités accessibles.
6. Actualiser les boutons et actions dépendant du statut.
7. Rafraîchir les données nécessaires des écrans concernés.
8. Faire en sorte que tout le changement soit immédiatement visible **sans déconnexion/reconnexion et sans quitter l'application**.

Mettre en place une logique centralisée de rafraîchissement afin d'éviter que chaque écran possède sa propre logique incohérente.

**Important :** le rafraîchissement doit être suffisamment complet pour qu'un utilisateur dont la demande CP vient d'être acceptée voie immédiatement son nouveau statut et toutes les fonctionnalités qui lui sont associées.

---

### 3. Corriger les doublons dans les résumés achetés et exclure les paiements échoués

Troisième problème : la gestion des achats de résumés présente actuellement un problème de doublon.

Scénario constaté :

1. L'utilisateur tente d'acheter un résumé.
2. La première tentative de paiement échoue.
3. L'utilisateur effectue une deuxième tentative.
4. La deuxième tentative réussit.
5. Dans l'historique des paiements, il est normal de voir :

   * une tentative échouée ;
   * puis une tentative réussie.
6. **Le problème apparaît dans la section "Résumés achetés" : le même résumé peut apparaître en double.**

L'historique des transactions doit conserver les différentes tentatives de paiement. En revanche, la liste des résumés réellement achetés doit représenter uniquement les achats effectivement validés.

#### À vérifier côté backend

Investiguer toute la logique permettant de déterminer si un résumé est acheté :

* modèle des paiements ;
* statut du paiement ;
* transactions ;
* relations utilisateur/résumé ;
* requêtes utilisées pour récupérer les résumés achetés ;
* éventuels doublons dans les relations ;
* logique exécutée après un paiement réussi ;
* traitement des paiements échoués.

Une tentative ayant le statut **échoué**, **failed**, **cancelled**, ou tout autre statut équivalent à un paiement non validé, **ne doit jamais permettre de considérer le résumé comme acheté**.

#### Règle métier à appliquer

La liste **"Résumés achetés"** doit respecter cette règle :

> Un résumé est considéré comme acheté uniquement lorsqu'il existe une transaction valide et confirmée pour cet utilisateur et ce résumé.

Les tentatives échouées doivent rester visibles dans **l'historique des paiements**, mais elles ne doivent jamais alimenter la liste des résumés achetés.

#### Protection contre les doublons

Ajouter également une protection afin que :

* un même résumé ne puisse apparaître deux fois dans "Résumés achetés" ;
* plusieurs transactions réussies concernant le même résumé ne créent pas plusieurs lignes dans la liste des résumés achetés ;
* la requête backend utilise une logique de déduplication appropriée ;
* le frontend ne duplique pas lui-même les résultats reçus du backend ;
* si nécessaire, utiliser une contrainte d'unicité ou une logique métier adaptée sur la relation utilisateur/résumé acheté.

**Important :** ne pas supprimer les transactions historiques. L'historique doit continuer à montrer les différentes tentatives de paiement. La correction concerne uniquement la manière dont les **résumés réellement achetés** sont déterminés et affichés.

### Résultat attendu

À la fin des corrections :

1. **Onboarding CP :** une fois finalisé, il ne réapparaît plus, même après navigation, retour arrière ou changement de page.
2. **Statut CP :** après acceptation de la demande, un simple rafraîchissement global suffit pour afficher immédiatement toutes les fonctionnalités CP, sans déconnexion/reconnexion.
3. **Résumés achetés :** seuls les achats réellement validés sont affichés, les paiements échoués sont exclus de cette liste et un même résumé ne peut jamais apparaître en double.

Avant de modifier le code, analyser les flux existants côté frontend et backend afin d'identifier les causes exactes. Éviter les correctifs superficiels basés uniquement sur l'interface : les règles métier doivent être sécurisées côté backend et correctement reflétées côté frontend.
