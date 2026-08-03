# Implémentation du badge de notifications sur l'icône de l'application

## Objectif

Mettre en place un **badge de notifications** sur l'icône de l'application (App Icon Badge), comme dans les applications modernes (WhatsApp, Gmail, Messenger, etc.).

## Contexte

Actuellement, lorsqu'il y a de nouvelles données ou de nouveaux messages, les notifications sont bien enregistrées et affichées à l'intérieur de l'application.

En revanche, lorsque l'utilisateur revient à l'écran d'accueil de son téléphone, **l'icône de l'application n'affiche pas le nombre de notifications non lues**.

## Fonctionnement attendu

Implémenter un badge sur l'icône de l'application qui respecte les règles suivantes :

* Chaque nouvelle notification non lue incrémente le compteur du badge.
* Le badge affiche le nombre exact de notifications non lues.
* Si l'utilisateur ouvre une notification ou marque toutes les notifications comme lues, le compteur est mis à jour automatiquement.
* Lorsque toutes les notifications ont été consultées, le badge disparaît (valeur = 0).
* Le badge doit rester synchronisé avec le nombre réel de notifications non lues enregistré dans l'application.

## Compatibilité

L'implémentation doit fonctionner sur :

* Android
* iOS

en utilisant les mécanismes natifs de chaque plateforme pour l'affichage des badges sur l'icône de l'application.

## Vérifications à effectuer

* Vérifier que le badge est mis à jour lorsqu'une nouvelle notification est reçue (application ouverte, en arrière-plan ou fermée).
* Vérifier que le badge est décrémenté lorsque des notifications sont lues.
* Vérifier que le badge est supprimé lorsqu'il n'existe plus aucune notification non lue.
* S'assurer que le compteur reste cohérent après un redémarrage de l'application ou du téléphone.

## Résultat attendu

Le comportement doit être identique à celui des applications modernes : l'utilisateur peut connaître immédiatement, depuis l'icône de l'application sur l'écran d'accueil de son téléphone, le nombre de notifications qu'il n'a pas encore consultées.
