## Objectif

Corriger la logique d’affectation dans l’onglet **Affectation / Signes vitaux** afin qu’un même patient ne puisse pas être enregistré ou affecté plusieurs fois pour une consultation le même jour.

### 1. Analyser l’existant

Avant toute modification :

* Analyser les modèles concernés : Patient, Signes vitaux, Consultation, Affectation et leurs relations.
* Analyser la logique actuelle d’enregistrement des signes vitaux et d’affectation à un médecin.
* Vérifier comment la date de consultation/séjour est actuellement déterminée.
* Vérifier s’il existe déjà une contrainte ou une validation similaire.

**Ne rien casser dans le fonctionnement existant.**

### 2. Nouvelle règle métier

Pour une même date :

* Un patient ne peut avoir **qu’une seule affectation/consultation**.
* Si le patient a déjà été affecté à un médecin pour une consultation à cette date, il ne doit pas être possible de créer une deuxième affectation ou une deuxième consultation pour ce même jour.
* La règle doit également empêcher un nouvel enregistrement de signes vitaux qui créerait une nouvelle consultation/affectation pour ce même patient et cette même date.

Exemple :

> Patient X → affecté au médecin A le 10/09/2026 → consultation créée.
> Patient X → tentative d’affectation au médecin B le 10/09/2026 → **refusée**.

Même si le médecin est différent, le patient ne doit pas avoir une deuxième consultation/affectation le même jour.

### 3. Gestion d’un séjour

Analyser également la notion de **séjour** existante dans le projet.

Si un patient possède déjà un enregistrement couvrant la journée concernée dans le cadre d’un séjour, ne pas créer un deuxième enregistrement de consultation/affectation pour cette même journée.

La règle doit utiliser les dates réelles du séjour et de la consultation selon le fonctionnement déjà présent dans le projet.

### 4. Backend obligatoire

La règle doit être appliquée **côté backend**, et pas uniquement dans l’interface.

Avant de créer l’enregistrement :

1. Rechercher si le patient possède déjà une consultation/affectation pour la date concernée.
2. Vérifier également les éventuels chevauchements liés au séjour.
3. Si un doublon existe, refuser la création.
4. Retourner une erreur métier claire au frontend.

Si cela est pertinent avec l’architecture actuelle, ajouter également une **contrainte d’unicité en base de données** pour renforcer cette règle.

### 5. Frontend

Dans l’onglet **Affectation / Signes vitaux** :

* Empêcher l'utilisateur de créer une deuxième affectation lorsque le patient est déjà enregistré pour cette journée.
* Afficher un message clair, par exemple :
  **« Ce patient possède déjà une consultation/affectation pour cette journée. Une nouvelle affectation n’est pas autorisée. »**
* Gérer également correctement l’erreur retournée par le backend afin qu’aucun doublon ne puisse être créé par une autre action ou un contournement de l’interface.

### 6. Vérifications

Tester au minimum :

* Patient sans consultation → création autorisée.
* Patient déjà affecté le même jour → deuxième affectation refusée.
* Patient affecté à un autre médecin le même jour → refusée.
* Patient ayant déjà une consultation le même jour → nouvelle consultation refusée.
* Patient avec séjour couvrant la date concernée → vérifier que le doublon est refusé selon la logique métier du séjour.
* Même patient à une date différente → création autorisée.
* Vérifier qu’aucune fonctionnalité existante de consultation, signes vitaux ou affectation n’est cassée.

**Important : analyser l’architecture actuelle avant de modifier le code et respecter les relations/modèles déjà existants. Ne pas créer de nouvelle logique parallèle si une logique existante peut être réutilisée.**

