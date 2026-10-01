## DEMANDE DE CP — NUMÉRO ET RÈGLES MÉTIER

### 1. Ajouter le numéro de téléphone

Dans le formulaire de demande de CP, les champs actuels restent obligatoires :

* Email
* Description

Ajouter également :

* **Numéro de téléphone — obligatoire**

Le numéro doit être **prérempli automatiquement avec le numéro de téléphone de l'utilisateur connecté**, mais rester modifiable manuellement.

Ne pas figer la valeur : l'utilisateur doit pouvoir remplacer le numéro avant la soumission.

Vérifier et respecter la structure existante côté backend et frontend sans casser le fonctionnement actuel.

---

### 2. Empêcher plusieurs demandes CP pour une même promotion

Appliquer cette règle **à la fois côté backend et frontend** :

Pour une même combinaison :

**Université + Filière + Promotion**

il ne peut exister qu'une seule demande CP active ou approuvée.

Une nouvelle demande doit être bloquée lorsqu'une demande existe déjà pour cette même combinaison avec un statut :

* **En attente/ en cours**
* **Approuvée / Validée**

#### Backend

Avant toute création de demande, effectuer systématiquement une vérification en base de données.

Si une demande active ou approuvée existe déjà pour la même université, filière et promotion :

* refuser la création ;
* retourner une réponse claire indiquant qu'une demande existe déjà.

Cette vérification backend doit rester la protection principale, même si le frontend masque correctement les actions.

#### Frontend

Après le chargement ou le rafraîchissement des données, vérifier l'existence d'une demande active/approuvée pour la combinaison Université + Filière + Promotion.

Si une demande existe :

* masquer les cards/boutons permettant de faire une nouvelle demande.

Si l'utilisateur tente malgré tout de soumettre une demande sans avoir rafraîchi l'écran :

* le backend doit bloquer la requête ;
* afficher un message approprié, par exemple :

  * **« Impossible de faire une nouvelle demande : une demande est déjà en cours. »**
  * **« Impossible de faire une nouvelle demande : une demande a déjà été validée. »**

### Cas où une nouvelle demande est autorisée

Une nouvelle demande doit être possible uniquement lorsqu'il n'existe **aucune demande en attente ou approuvée** pour cette combinaison.

Si la demande précédente a été :

* **désapprouvée / rejetée / invalidée**

alors l'utilisateur doit pouvoir effectuer une nouvelle demande.

Le frontend doit donc réafficher la possibilité de faire une demande dans ce cas.

### Règle finale

**Demande en attente/ en cours → nouvelle demande interdite**

**Demande approuvée → nouvelle demande interdite**

**Demande rejetée/désapprouvée/invalidée → nouvelle demande autorisée**

Appliquer impérativement cette logique **dans les deux couches : frontend + backend**, sans modifier les autres règles existantes du système.
