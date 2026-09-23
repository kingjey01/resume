Prompt à ajouter
3. Affichage incorrect des formules mathématiques, physiques, etc.

Dans les résumés contenant des formules mathématiques, physiques, chimiques ou expressions scientifiques, certaines formules sont actuellement affichées sous forme brute avec des caractères comme $, \vec{}, \, etc., au lieu d’être rendues correctement pour l’utilisateur, comme le montre l’image fournie.

Analyser d’abord comment les formules sont générées par DeepSeek, stockées par le backend et transmises à Flutter.
Identifier le format actuellement utilisé (LaTeX, Markdown, texte brut, etc.) et déterminer pourquoi Flutter affiche les instructions/formules brutes au lieu de leur rendu mathématique.
Implémenter un rendu propre et lisible des formules dans les résumés : vecteurs, fractions, puissances, indices, équations, symboles mathématiques, etc.
Le rendu doit être visuellement distinct du texte normal, comme le bloc FORMULE déjà prévu, tout en restant parfaitement lisible.
Cette logique doit également fonctionner pour les formules mathématiques, physiques et chimiques, sans casser le rendu actuel des blocs de code/programmes.
Vérifier également les contenus déjà enregistrés en base afin que le nouveau rendu puisse les afficher correctement sans devoir régénérer tous les résumés.
⚠️ Sécurité avant modification

Avant de modifier un quelconque fichier backend ou la logique de génération/rendu :

Identifier précisément les fichiers qui seront modifiés.
Faire une copie de sauvegarde de chaque fichier avant toute modification.
Ne modifier ensuite que les fichiers strictement nécessaires.
Tester le nouveau rendu avec plusieurs exemples de formules.
Vérifier que les résumés normaux et les blocs de code continuent de fonctionner exactement comme avant.
En cas de régression, pouvoir restaurer immédiatement les fichiers sauvegardés.

Ne rien modifier d'autre dans la logique existante. L'objectif est uniquement de corriger le rendu des formules et d'ajouter cette prise en charge proprement.