## IMPLÉMENTATION DE L'ONBOARDING GÉNÉRAL — 2 PAGES

Implémenter l'onboarding général de première connexion à partir du design fourni dans l'image de référence.

**IMPORTANT :** ne pas créer un nouveau design. Reproduire fidèlement le style visuel de la maquette : thème bleu moderne, fond principalement blanc, textes noirs/bleu foncé, boutons bleus, illustrations, cartes arrondies, icônes et éléments graphiques triangulaires/décoratifs.

Avant toute modification, analyser le code existant et réutiliser les composants, styles, navigation et logique d'onboarding déjà présents dans le projet. Ne rien casser dans le workflow actuel de première connexion, de profil ou d'onboarding CP.

### PAGE 1 — Découvrir les résumés gratuits

Créer la première page de l'onboarding général.

Reprendre le design de la première interface de l'image :

* fond blanc ;
* éléments graphiques bleus ;
* illustration liée aux études, aux livres et à l'IA ;
* titre principal en français ;
* texte explicatif ;
* petites cartes/icônes présentant les avantages ;
* indicateur de progression ;
* bouton/option « Passer » si cette fonctionnalité existe déjà dans le système actuel.

Texte principal :

**« Découvrez des résumés générés par IA »**

Texte secondaire :

**« Accédez à des résumés complets générés par intelligence artificielle, spécialement adaptés à votre domaine d’étude. »**

Utiliser des éléments visuels similaires à la maquette pour présenter notamment :

* des résumés clairs et complets ;
* l'approfondissement des connaissances ;
* une meilleure orientation dans les études.

La page doit être responsive et adaptée aux différentes tailles d'écran Flutter.

---

### PAGE 2 — Continuer vers l'application

Après avoir terminé la première page, afficher la deuxième interface.

Reprendre le même langage visuel que la première page afin que les deux écrans forment un onboarding cohérent.

Utiliser :

* fond blanc ;
* thème bleu ;
* illustration représentant la consultation de contenus/résumés ;
* éléments décoratifs triangulaires ;
* titre principal ;
* texte explicatif ;
* indicateur de progression ;
* grand bouton bleu « Continuer ».

Titre :

**« Commencez dès maintenant ! »**

Texte :

**« Explorez les résumés gratuits disponibles et profitez pleinement de Résumé Plus pour exceller dans vos études. »**

Ajouter une zone informative indiquant que des résumés gratuits correspondant au domaine d'étude de l'utilisateur sont disponibles.

Lorsque l'utilisateur appuie sur **« Continuer »** :

1. enregistrer que l'onboarding général a été terminé ;
2. mettre à jour le state utilisateur ;
3. ne plus afficher cet onboarding lors des prochaines connexions ;
4. rediriger vers **l'Accueil existant**.

Ne pas créer ou modifier une nouvelle interface d'accueil. L'accueil actuel doit simplement afficher les données déjà prévues par la logique existante, notamment les résumés gratuits correspondant au profil de l'utilisateur.

### ORDRE D'IMPLÉMENTATION

Implémenter strictement dans cet ordre :

**Page 1 → Page 2 → validation de la navigation → intégration dans le workflow de première connexion.**

Ne pas modifier la détection actuelle de première connexion.

Le workflow final doit rester :

**Première connexion → renseignement du profil → onboarding général (Page 1 → Page 2) → Accueil**

L'onboarding CP existant doit rester indépendant et ne doit pas être déclenché ou modifié par cette nouvelle fonctionnalité.

### DESIGN

L'image fournie constitue la **référence visuelle principale**.

Respecter autant que possible :

* les proportions ;
* les espacements ;
* la hiérarchie typographique ;
* les couleurs ;
* les formes arrondies ;
* les boutons ;
* les illustrations ;
* les icônes ;
* les éléments décoratifs bleus ;
* les indicateurs de progression.

Ne pas remplacer la maquette par un design personnel.

Réutiliser les composants Flutter existants lorsque cela est possible et créer uniquement les composants nécessaires à ces deux écrans.
