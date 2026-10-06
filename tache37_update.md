Prompt 1 — Renommer complètement l’application en « Muhtasari+ »
Analyse d’abord tout le projet avant modification.
L’application « Résumé Plus » doit maintenant être renommée « Muhtasari+ ».
Remplacer uniquement les références liées au nom de l’application, sans modifier la logique métier, les API, les modèles, les routes, les fonctionnalités ou les données existantes.
Vérifier notamment :
- Nom affiché sous l’icône de l’application sur Android.
- Nom affiché au lancement de l’application.
- app_name / configuration Android et Flutter concernée.
- Splash screen et éventuels écrans d’accueil.
- Titres, headers et textes visibles dans l’application.
- Onboarding.
- Pages de connexion/inscription.
- Notifications si le nom de l'application y apparaît.
- Conditions d'utilisation.
- Politique de confidentialité.
- Mentions légales et autres textes présentant l'application.
- Métadonnées locales utilisées pour le nom de l'application.
Faire une recherche globale de « Résumé Plus », « Resume Plus » et éventuelles variantes directement liées au nom commercial afin d'identifier toutes les occurrences pertinentes.
Important :
- Ne pas renommer les noms techniques internes si cela n'est pas nécessaire au fonctionnement.
- Ne pas modifier les noms de packages, IDs, endpoints, modèles ou structures backend uniquement pour changer le nom commercial.
- Ne pas créer de régression.
- Après modification, vérifier qu'aucune référence visible à « Résumé Plus » ne subsiste lorsqu'elle devrait afficher « Muhtasari+ ».
Prompt 2 — Centrer les boutons « Écouter » et « Reprendre »
Corriger uniquement la présentation frontend des boutons « Écouter » et « Reprendre » dans le détail d'un résumé.
Actuellement, lorsque l'espace horizontal est insuffisant, les boutons passent correctement en disposition verticale, mais ils restent alignés à gauche dans leur conteneur.
Correction demandée :
- Conserver le comportement responsive existant.
- Lorsque les boutons sont en ligne : conserver leur disposition actuelle.
- Lorsqu'ils passent en colonne : centrer horizontalement les deux boutons dans leur conteneur.
- Empêcher tout overflow, décalage ou mauvaise position.
- Utiliser la solution responsive adaptée (Flex, Column, Wrap, contraintes de largeur, alignment, etc.).
- Vérifier le comportement sur petits et grands écrans.
Règle stricte de non-régression : ne toucher qu'à la mise en forme et au positionnement de ces deux boutons. Ne modifier ni la logique audio, ni les états, ni les API, ni les autres éléments du détail du résumé.