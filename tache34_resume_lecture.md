1. Indicateur « résumé déjà vu / non vu »
Dans les onglets Résumés, distinguer visuellement les résumés auxquels l'utilisateur n'a encore jamais accédé de ceux qu'il a déjà consultés.
Reprendre le principe déjà utilisé pour les notifications :
- Résumé non consulté → petit point bleu + fond gris/translucide.
- Dès que l'utilisateur ouvre le résumé → le marquer comme vu.
- Résumé déjà consulté → supprimer le point bleu et le fond gris.
- La distinction doit être gérée côté Flutter/front-end et être propre à l'utilisateur connecté.
- Vérifier d'abord la logique actuelle afin de ne pas créer un système qui entre en conflit avec le cache ou les états existants.
- Le statut « vu » doit rester cohérent lorsqu'on navigue entre les onglets ou qu'on revient sur l'application.
2. Lecture audio à partir de la page courante
La lecture audio d'un résumé fonctionne actuellement correctement, mais elle recommence toujours à la première page.
Modifier uniquement ce comportement :
- Page 1 → lecture depuis la page 1.
- Page 5 → lecture directement depuis la page 5.
- Continuer ensuite la lecture normalement jusqu'à la fin du résumé.
- Ne pas recommencer automatiquement depuis le début lorsque l'utilisateur lance la lecture depuis une page donnée.
- Conserver la pagination, la lecture actuelle et tous les comportements existants.
- Utiliser l'état/page actuellement affiché comme point de départ de la lecture.
3. Masquer complètement la demande de CP lorsque celle-ci n'est plus possible
Actuellement, le card « Faire une demande de CP » devient parfois grisé avec un message lorsque l'utilisateur possède déjà une demande ou un CP.
Améliorer ce comportement :
Si la base indique qu'il existe déjà, pour la même université + promotion + filière :
- une demande en attente ;
- une demande acceptée/validée ;
- ou un CP déjà existant ;
→ ne pas afficher du tout le card de demande de CP.
Le contrôle doit être effectué avec les données actuelles au chargement/rafraîchissement de la page afin d'éviter un état obsolète.
Conserver la règle métier backend existante comme protection finale, même si le card est masqué côté Flutter.
4. Correction responsive des boutons audio
Analyse uniquement la mise en page frontend du détail d’un résumé. Ne modifie aucune logique métier, aucun endpoint, aucun état, aucune API et aucune fonctionnalité existante.
Problème : sur les petits écrans, les boutons Play/Pause et reprendre débordent de leur conteneur et décalent le contenu du résumé.
Correction demandée :
- Rendre cette zone totalement responsive.
- Empêcher tout overflow, oversize ou débordement horizontal.
- Adapter automatiquement la disposition selon la largeur disponible.
- Utiliser une approche Flex/Grid responsive appropriée.
- Lorsque l’espace est insuffisant, les boutons doivent pouvoir s’empiler verticalement au lieu de se chevaucher ou sortir du conteneur.
- Conserver exactement le design, les couleurs, les tailles et les fonctionnalités actuelles autant que possible.
- Vérifier le comportement sur plusieurs petites et grandes tailles d’écran.

Règle stricte de non-régression : ne toucher qu’à la présentation responsive de cette zone. Ne rien modifier d’autre dans l’application.
Important : analyser d'abord le code existant et réutiliser les mécanismes déjà présents. Ne pas refaire inutilement ce qui existe. Modifier uniquement ce qui est nécessaire et vérifier qu'aucune régression n'est introduite.