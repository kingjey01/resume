Analyse la logique actuelle des brouillons audio dans l’application.

Problème constaté : lorsqu’un utilisateur commence un enregistrement audio et que l’application indique qu’un brouillon existe, l’enregistrement semble être perdu dès que l’utilisateur quitte l’interface de création/enregistrement du résumé audio.

Vérifie précisément :

* où l’audio est actuellement stocké pendant l’enregistrement ;
* à quel moment la session ou le brouillon est supprimé ;
* ce qui se passe lorsque l’utilisateur quitte l’écran, revient en arrière ou ferme l’interface ;
* si une ancienne logique de sauvegarde locale des brouillons a été supprimée lors des dernières modifications ;
* les interactions entre le stockage local, l’état Flutter et la soumission vers le backend.

Ne modifie pas encore le code. Identifie d’abord la cause exacte de la perte du brouillon et indique les fichiers et fonctions concernés.
Corrige la gestion des brouillons audio.

Règles obligatoires :

1. Dès qu’un utilisateur commence ou termine un enregistrement, l’audio doit être conservé localement sur l’appareil.
2. Le brouillon doit rester disponible même si l’utilisateur :

   * quitte l’écran d’enregistrement ;
   * revient en arrière ;
   * ferme puis rouvre l’interface concernée ;
   * n’a aucune connexion Internet.
3. Quitter l’écran ne doit JAMAIS supprimer automatiquement le brouillon.
4. Le brouillon doit être supprimé uniquement lorsque l’utilisateur choisit explicitement de le supprimer.
5. Maximum 5 audios brouillons peuvent être conservés simultanément en local.
6. Si les 5 emplacements sont occupés, empêcher la création d’un sixième brouillon et afficher un message approprié.
7. Chaque brouillon doit conserver au minimum les informations nécessaires pour reprendre ou soumettre l’audio : fichier audio local, titre éventuel, professeur/cours si déjà renseignés et métadonnées nécessaires.
8. La présence d’un brouillon doit être persistante et récupérable après redémarrage de l’application.
9. La soumission du brouillon vers le backend doit être une action distincte. Une fois soumis avec succès, le fichier local correspondant peut être supprimé selon la logique existante.
10. Ne pas dépendre de la connexion Internet pour créer, conserver ou consulter les brouillons.

Conserve autant que possible l’architecture actuelle et réutilise la logique locale existante si elle existe. Évite de créer un deuxième système de stockage inutile.

Avant de modifier le code, identifie les fichiers concernés et explique brièvement la solution retenue. Puis implémente la correction.
Après la correction, vérifie complètement le comportement des brouillons audio.

Teste au minimum ces scénarios :

* [ ] Créer un audio puis quitter l’écran : le brouillon reste disponible.
* [ ] Créer un audio sans connexion Internet : le brouillon reste disponible.
* [ ] Fermer et rouvrir l’application : le brouillon est toujours présent.
* [ ] Créer plusieurs brouillons : jusqu’à 5 maximum.
* [ ] Tenter de créer un 6e brouillon : l’opération est bloquée proprement.
* [ ] Supprimer explicitement un brouillon : seul ce brouillon est supprimé.
* [ ] Quitter l’écran sans supprimer : aucun fichier audio n’est supprimé.
* [ ] Reprendre un brouillon existant : ses données sont correctement restaurées.
* [ ] Soumettre un brouillon avec Internet : l’audio est envoyé pour transcription/résumé.
* [ ] Vérifier qu’un échec de soumission ne supprime pas le brouillon local.
* [ ] Vérifier qu’une soumission réussie applique correctement la suppression ou l’archivage local prévu.

Vérifie également qu’aucune modification récente n’a réintroduit une suppression automatique lors du changement d’écran ou de l’arrêt de la session d’enregistrement.
