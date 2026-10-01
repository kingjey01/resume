1. Gestion du State et isolation des données entre utilisateurs
PROBLÈME 1 — ISOLATION DES DONNÉES ENTRE UTILISATEURS

Il existe un problème de gestion du state lors du changement de compte sur le même téléphone.

Scénario :
- Utilisateur A se connecte et consulte ses données.
- Utilisateur A se déconnecte.
- Utilisateur B se connecte sur le même téléphone.
- Certaines données de l'utilisateur A restent affichées dans le compte de B.

Cela indique probablement qu'un state, cache, provider, controller ou donnée persistante n'est pas correctement réinitialisé lors du logout/login.

Analyser toute la chaîne de gestion d'authentification et de données utilisateur.

Objectif :
- Chaque utilisateur doit voir uniquement ses propres données.
- Lors d'une déconnexion, les states et données dépendant de l'utilisateur précédent doivent être invalidés/réinitialisés.
- Lors d'une nouvelle connexion, les données doivent être rechargées selon le nouvel utilisateur authentifié.
- Aucun cache local ou state persistant ne doit permettre à l'utilisateur B de voir les données de A.
- Vérifier également que les filtres côté API/backend utilisent bien l'utilisateur authentifié.

Corriger la cause réelle du problème plutôt que d'ajouter uniquement un rafraîchissement visuel.

La séparation des données doit rester correcte même lorsque plusieurs comptes sont utilisés successivement sur le même appareil.
2. Mauvaise navigation après génération d'un QCM
PROBLÈME 2 — NAVIGATION APRÈS GÉNÉRATION DU QCM

Lorsqu'un QCM est généré avec succès, l'application n'affiche pas directement l'interface permettant de répondre aux questions.

À la place, elle revient ou affiche une interface permettant de sélectionner le niveau/type d'exercice, comme si le QCM n'avait pas encore été généré.

Analyser le workflow complet :

Génération → réponse API → récupération du QCM → state → navigation → affichage des questions.

Déterminer si le problème vient :
- du state ;
- de la réponse de l'API ;
- de l'identifiant du questionnaire généré ;
- du filtrage ;
- ou de la navigation Flutter.

Après une génération réussie, l'utilisateur doit être automatiquement dirigé vers l'interface du questionnaire généré et pouvoir commencer directement l'exercice.

Ne pas lui redemander de choisir le niveau ou de relancer la génération.

Conserver la logique existante de génération et corriger uniquement le workflow de navigation/état responsable de ce comportement.
3. Bouton retour Android / navigation système après les résultats
PROBLÈME 3 — RETOUR SYSTÈME APRÈS LES RÉSULTATS D'UNE TENTATIVE

Après avoir terminé un exercice et consulté les résultats de la tentative, le bouton retour système du téléphone provoque un comportement incorrect :

- écran noir ;
- page de téléchargement ;
- blocage ;
- ou navigation vers une page inattendue.

Le bouton retour interne de l'application fonctionne, mais le retour système du téléphone doit également fonctionner correctement.

Corriger la gestion de la navigation et de la pile de routes Flutter afin que :

- le bouton retour de l'application fonctionne ;
- le bouton retour système Android fonctionne ;
- aucun écran noir ne soit affiché ;
- aucune page de téléchargement ne soit ouverte involontairement ;
- aucune route invalide ne soit conservée dans la navigation.

Analyser la stack de navigation utilisée pour :

Questionnaire → Tentative → Résultats → Retour.

Le retour système doit ramener l'utilisateur vers l'écran logique précédent, exactement comme le bouton retour de l'application.

Ne pas contourner le problème avec une simple redirection arbitraire : corriger la gestion réelle de la navigation et de la stack des routes.