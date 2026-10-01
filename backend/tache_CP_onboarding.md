
Problème identifié
Le rafraîchissement manuel (via l'icône de rafraîchissement) ne recharge pas complètement l'application. Le onboarding CP ne s'affiche qu'après un redémarrage complet de l'app (mise en arrière-plan / retour).

Objectif
Faire en sorte que le rafraîchissement de la page (via l'icône de rafraîchissement ) déclenche un rechargement total de l'application, permettant ainsi d'afficher immédiatement le onboarding CP après acceptation de la demande.

Actions à réaliser

Vérifier la logique existante

Examiner le code actuel qui gère l'acceptation d'une demande CP.

Vérifier comment le statut CP est stocké (localStorage, sessionStorage, cookies, ou token).

Vérifier comment le onboarding CP est déclenché (condition d'affichage).

Corriger le comportement du rafraîchissement

S'assurer que l'icône de rafraîchissement (ou tout rechargement de page) effectue un hard reset complet de l'application :

Réinitialisation du state .

Re-vérification du statut CP auprès du serveur (ou du stockage local).


Tester les cas suivants

Après acceptation CP → rafraîchir → le onboarding CP s'affiche.

Après refus CP → rafraîchir → le onboarding ne s'affiche pas.

Résultat attendu
Un rafraîchissement de page (même simple) suffit pour que l'application détecte le nouveau statut CP et affiche le onboarding correspondant, sans avoir à quitter l'application.

Note : Si le rafraîchissement ne suffit pas à lui seul, envisager d'ajouter un setTimeout ou un useEffect qui force la re-vérification du statut CP à chaque chargement de page.

