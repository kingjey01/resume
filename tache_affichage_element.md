Analyse et corrige uniquement le problème de **synchronisation de l’état utilisateur/CP après connexion** dans l’application.

### 1. Analyse préalable — ne rien modifier

Commence par analyser le fonctionnement actuel :

* récupération des informations de l’utilisateur après connexion ;
* récupération et stockage de son rôle/statut CP ;
* restauration de session lorsque l’application revient de l’arrière-plan ou est relancée ;
* état utilisé pour afficher/masquer les cards de **demande de CP** ;
* état utilisé pour afficher le **bouton `+` du Scaffold** ;
* filtres et conditions actuellement utilisés côté frontend ;
* moment où ces états sont chargés et mis à jour ;
* éventuels problèmes de cache ou d’état initial.

**Ne modifie aucun fichier pendant cette phase.**

### 2. Logique métier existante à préserver

La logique métier côté backend est déjà correcte et doit rester **strictement inchangée**.

Actuellement, le backend empêche déjà correctement :

* de refaire une demande lorsqu’une demande est déjà en attente ;
* de refaire une demande lorsqu’un CP existe déjà pour la même université / promotion / filière ;
* toute autre soumission qui ne respecte pas les règles métier existantes.

**Ne touche absolument pas à ces règles backend.**

Le problème concerne uniquement l’affichage et la synchronisation de l’état côté frontend.

### 3. Problème actuel

Lorsqu’un utilisateur est déjà **CP validé** et accède à son espace personnel:

* l’utilisateur est correctement authentifié ;
* il entre correctement dans son espace personnel ;
* mais les cards permettant de faire une demande de CP s’affichent encore temporairement ;
* le bouton `+` permettant d’accéder aux créations n’apparaît pas immédiatement.

Actuellement, un **rafraîchissement manuel de la page** corrige la situation :

* les cards disparaissent ;
* le bouton `+` apparaît ;
* l’interface correspond alors correctement au statut CP de l’utilisateur.

Ce rafraîchissement manuel ne doit cependant **pas être nécessaire**.

### 4. Comportement attendu

Dès que l’utilisateur est authentifié et que son état réel est connu :

#### Si l’utilisateur est déjà CP

L’interface doit immédiatement :

* détecter son statut CP ;
* masquer les cards de demande de CP ;
* afficher le bouton `+` du Scaffold ;
* permettre l’accès aux fonctionnalités de création prévues pour un CP.

Aucun rafraîchissement manuel ne doit être nécessaire.

#### Si l’utilisateur n’est pas CP

* respecter les conditions existantes ;
* ne pas afficher le bouton `+` réservé au CP.

#### Si une demande CP est déjà en attente

Les cards concernées doivent rester masquées conformément à la logique métier existante.

#### Si un CP existe déjà pour la combinaison concernée

Les cards doivent également rester masquées.

### 5. Connexion et restauration de l’application

Le comportement doit être correct dans tous ces cas :

1. première ouverture après connexion ;
2. reconnexion d’un utilisateur existant ;
3. application sortie de l’arrière-plan puis restaurée ;
4. application retirée des tâches puis relancée ;
5. restauration d’une session déjà authentifiée.

Dans chacun de ces cas, l’interface doit utiliser **l’état réel et actuel de l’utilisateur**, sans nécessiter un refresh manuel.

### 6. Card de demande CP et bouton `+`

Vérifie particulièrement si les cards et le bouton `+` utilisent :

* deux états différents ;
* un état initial obsolète ;
* des données utilisateur chargées après le rendu initial ;
* un provider/controller/state manager qui n’est pas rafraîchi après authentification ;
* un cache local non synchronisé ;
* une condition de filtrage exécutée trop tôt.

Si les deux éléments dépendent du même statut utilisateur, privilégie **une source d’état cohérente et réactive**, adaptée à l’architecture actuelle.

### 7. Ne pas modifier inutilement

IMPORTANT :

* ne change pas le backend ;
* ne change pas les règles métier ;
* ne change pas les API existantes ;
* ne change pas les endpoints ;
* ne change pas le design ;
* ne change pas les cards elles-mêmes ;
* ne change pas le fonctionnement du bouton `+` ;
* ne touche pas aux fonctionnalités CP existantes ;
* ne modifie aucune autre partie de l’application.

Corrige uniquement le problème de **détection et de propagation de l’état CP après authentification/restauration de session**.

### 8. Tests de non-régression

Vérifie obligatoirement :

* utilisateur déjà CP → cards masquées immédiatement + bouton `+` visible ;
* utilisateur non CP → comportement actuel conservé ;
* demande CP en attente → card masquée ;
* CP déjà existant pour la promotion/filière/université → card masquée ;
* reconnexion → état correct sans refresh ;
* retour depuis l’arrière-plan → état correct ;
* relance de l’application → état correct ;
* refresh manuel → fonctionnement toujours correct.

### Objectif final

Le comportement attendu est simple :

> **Dès que l’utilisateur entre dans son espace, l’interface doit connaître son statut réel et afficher immédiatement les bons éléments. Un utilisateur déjà CP ne doit jamais avoir besoin de rafraîchir manuellement la page pour faire disparaître les cards de demande et faire apparaître le bouton `+`.**

Ne fais aucune autre modification.
