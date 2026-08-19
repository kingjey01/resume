# Correction des bugs côté étudiant — Résumés, QCM et pagination

Corriger les problèmes suivants côté **Étudiant**, sans casser les comportements déjà fonctionnels côté **CP**.

Avant toute modification, analyser la logique existante de contrôle d'achat, d'affichage des résumés, de lancement des QCM et de pagination. Réutiliser les mécanismes déjà fonctionnels côté CP lorsque cela est pertinent.

## 1. Résumé non acheté : cadenas et contenu verrouillé

Règle métier :

Lorsqu'un étudiant **n'a pas acheté un résumé** :

* le résumé doit être considéré comme verrouillé ;
* afficher le cadenas ;
* afficher uniquement la partie d'introduction autorisée ;
* cette partie doit être visuellement grisée/masquée selon le comportement actuel ;
* le reste du résumé doit rester inaccessible.

Bug actuel :

Le cadenas disparaît parfois alors que l'étudiant n'a pas acheté le résumé, tout en laissant apparaître seulement une petite partie du contenu.

Corriger la propagation et la vérification de l'état d'achat afin que l'interface reflète immédiatement et strictement le véritable statut :

**acheté → contenu complet**

**non acheté → cadenas + aperçu limité**

Ne pas se baser uniquement sur un état local obsolète.

---

## 2. Empêcher le lancement du QCM pour un résumé non acheté

Un étudiant ne doit **jamais pouvoir lancer un QCM à partir d'un résumé qu'il n'a pas acheté**, même s'il possède un abonnement QCM.

Avant de permettre le lancement du QCM, vérifier que le résumé concerné est acheté.

Si le résumé n'est pas acheté :

* bloquer l'accès au QCM ;
* afficher un message indiquant que l'étudiant doit d'abord acheter le résumé.

Cette règle doit être appliquée côté interface **et côté backend/API**, afin qu'elle ne puisse pas être contournée.

---

## 3. Pagination des résumés achetés côté étudiant

Dans :

**Acheter → Consulter les résumés achetés**

la pagination n'est actuellement pas correctement appliquée côté étudiant.

Bug :

Les contenus longs sont affichés de manière excessive sur une seule ligne ou sans respecter correctement la mise en page, obligeant l'utilisateur à faire un très long scroll.

Le comportement de pagination déjà fonctionnel côté **CP** doit être analysé et réutilisé/adapté côté étudiant.

Vérifier notamment :

* pagination API ;
* nombre d'éléments par page ;
* gestion de `page` / `offset` / `limit` selon l'implémentation actuelle ;
* affichage Flutter ;
* navigation entre les pages ;
* retour/chargement de la page suivante.

Ne pas réinventer la pagination si une implémentation fonctionnelle existe déjà côté CP.

## Contraintes

Ne pas modifier les règles métier existantes.

Ne pas casser :

* l'accès complet aux résumés achetés ;
* les abonnements QCM ;
* le fonctionnement côté CP ;
* les mécanismes de paiement.

Identifier d'abord les différences entre les implémentations **CP** et **Étudiant**, puis corriger uniquement les parties responsables de ces trois problèmes.
