PROBLÈME 1 — Fuite de données entre comptes et cache persistant

Le problème d'isolation des données entre utilisateurs est seulement partiellement corrigé.

Reproduire précisément ce scénario :

Connexion avec le compte A.
Consultation de l'application.
Déconnexion.
Connexion avec le compte B sur le même appareil.

Constat actuel :

Accueil → Résumés récents : les résumés du compte A restent affichés.
Accueil → Parcourir les cours : correct, les données du compte B sont bien affichées.
Onglet Résumés : les résumés du compte A restent affichés.
Onglet Validation : correct, les données du compte B sont affichées.
Mes achats → Résumés achetés : les données du compte A restent affichées.
Mes achats → Historique des paiements : les données du compte A restent affichées.
Exercices → Mes tentatives : correct, les données du compte B sont affichées.
Travail demandé

Utiliser les écrans qui fonctionnent correctement comme référence, notamment Validation et Mes tentatives, et comparer leur mécanisme de chargement, filtrage, state et rafraîchissement avec :

Résumés récents ;
Onglet Résumés ;
Résumés achetés ;
Historique des paiements.

Identifier précisément pourquoi certaines données restent en cache après le changement de compte.

Corriger la gestion du state/cache afin que, lors du logout ou du changement d'utilisateur :

les données liées au compte A soient invalidées ;
les providers/controllers/states concernés soient réinitialisés ;
les données du compte B soient rechargées ;
aucune donnée du compte précédent ne puisse rester affichée temporairement ou définitivement.

Ne pas ajouter uniquement un refresh visuel. Identifier et corriger la cause réelle de la persistance des anciennes données.

Vérifier également que le backend filtre systématiquement les données selon l'utilisateur authentifié.

PROBLÈME 2 — Notification lors du passage à « Résumé disponible »

Dans le workflow de traitement d'une session audio, les statuts évoluent notamment vers :

En attente → En traitement → Transcrit → Résumé disponible

Actuellement, lorsque le résumé devient Transcrit ou surtout Résumé disponible, la notification destinée à l'utilisateur/CP n'est pas toujours déclenchée.

L'utilisateur peut donc avoir un résumé terminé sans savoir qu'il doit aller le valider.

Travail demandé

Analyser le workflow complet :

Session → transcription → changement de statut → génération du résumé → Résumé disponible → notification

Vérifier :

où et comment le statut est modifié ;
quelle tâche/service déclenche ces changements ;
où la notification est actuellement déclenchée ;
pourquoi elle peut ne pas être exécutée ;
si les tâches asynchrones concernées sont correctement exécutées ;
si une condition ou un changement de statut empêche l'envoi.

La règle métier doit être :

Dès qu'un résumé passe effectivement au statut « Résumé disponible », une notification doit être déclenchée pour informer l'utilisateur qu'il peut consulter/valider son résumé.

Éviter les notifications en double lors des mises à jour ultérieures du même résumé.

Corriger le déclenchement à la source du changement de statut plutôt que de simplement ajouter un mécanisme de polling côté Flutter.