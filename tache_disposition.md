L’application **Résumé Plus** fonctionne actuellement correctement.

La logique métier, les exercices, les résumés et toutes les fonctionnalités existantes sont déjà validés.

Je veux intervenir **uniquement sur le design et l’affichage**, sans modifier la logique fonctionnelle.

### 1. Analyse préalable — aucune modification

Commence par analyser entièrement la partie concernée :

* l’écran de **détail d’un résumé** ;
* la zone qui affiche les informations du résumé ;
* l’affichage du **nom d’utilisateur** ;
* l’affichage de la **date** ;
* l’affichage du **prix/montant du résumé** ;
* la structure actuelle de cette zone ;
* les contraintes de largeur et de responsive design déjà utilisées.

**À cette étape, ne modifie absolument rien.**

### 2. Problème à corriger

Le problème concerne uniquement la zone du détail du résumé où sont affichés :

* le nom de l’utilisateur ;
* la date ;
* le prix/montant du résumé.

Lorsque le **nom d’utilisateur est très long**, il dépasse la largeur disponible et provoque un débordement (`overflow`).

Ce débordement peut notamment :

* pousser ou chevaucher le prix ;
* déformer la disposition ;
* faire sortir certains contenus de leur zone ;
* provoquer un affichage trop large sur les petits écrans.

### 3. Correction souhaitée

Corrige uniquement la mise en page de cette zone.

Si le nom d’utilisateur est trop long pour tenir dans l’espace disponible :

* il doit pouvoir **passer sur plusieurs lignes** ;
* la disposition doit s’adapter naturellement en **colonne lorsque l’espace horizontal devient insuffisant** ;
* le nom ne doit jamais forcer le prix ou les autres informations à sortir de leur conteneur ;
* aucun élément ne doit dépasser la largeur disponible ;
* éviter tout `overflow-x` ou débordement horizontal ;
* conserver un affichage propre sur mobile comme sur les écrans plus larges.

La priorité est que **chaque élément reste contenu dans sa propre zone**, même avec un nom extrêmement long.

### 4. Contraintes strictes

**Ne touche à rien d’autre.**

Ne modifie pas :

* la logique des résumés ;
* la logique des exercices/QCM ;
* les données ;
* les API ;
* les modèles ;
* les calculs ;
* les prix ;
* les dates ;
* les fonctionnalités existantes ;
* la navigation ;
* les autres écrans ;
* les autres composants ;
* le design général de l’application.

Ne fais **aucune refonte graphique**.

Ne change pas les couleurs, tailles, espacements ou composants qui ne sont pas directement nécessaires pour résoudre ce problème.

### 5. Objectif final

Le résultat attendu est simplement :

> **Un nom d’utilisateur très long ne doit plus jamais provoquer de débordement ou de chevauchement avec le prix, la date ou les autres informations du détail du résumé. La zone doit automatiquement s’adapter et passer en disposition verticale/colonne lorsque nécessaire.**

Conserve exactement le fonctionnement actuel de l’application et le design existant autant que possible.

Après la modification, vérifie le comportement avec :

* un nom court ;
* un nom moyen ;
* un nom très long ;
* un petit écran/mobile ;
* un écran plus large.

**Aucune autre modification ne doit être effectuée.**
