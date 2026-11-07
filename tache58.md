Prompt 1 — Empêcher la suppression des cours ayant déjà un résumé générique
Dans l’application Flutter et le backend Django, empêcher un professeur de cours (CP) de supprimer un cours lorsqu’un résumé générique a déjà été créé pour ce cours.
- Vérifier cette règle côté backend, afin qu’elle ne puisse pas être contournée depuis l’interface.
- Afficher un message explicite : « Impossible de supprimer ce cours, car un résumé générique a déjà été créé pour celui-ci. »
- Conserver le comportement actuel pour les cours qui ne possèdent pas encore de résumé générique, selon les permissions existantes.
Ne modifier aucune autre règle métier.
Prompt 2 — Corriger la sauvegarde des audios en arrière-plan sur Android et iOS
L’enregistrement du micro en arrière-plan fonctionne désormais correctement, mais la sauvegarde et l’envoi des fichiers audio vers le serveur échouent lorsque l’application passe en arrière-plan ou que le téléphone est verrouillé. L’application affiche alors une erreur de connexion réseau. Le problème se manifeste sur Android et iOS, notamment lorsque l’utilisateur revient dans l’application.
Effectue une investigation approfondie pour identifier la cause réelle :
- Examiner le mécanisme d’upload, les timeouts, les interruptions réseau, le cycle de vie de l’application et la gestion des requêtes HTTP.
- Vérifier si les requêtes sont interrompues lorsque l’application passe en arrière-plan et si le mécanisme actuel est adapté aux restrictions de chaque plateforme.
- Implémenter une solution adaptée à Android et iOS pour que l’envoi puisse continuer en arrière-plan ou reprendre automatiquement après une interruption.
- Préserver le fichier audio local et l’état de progression jusqu’à la confirmation de réception par le serveur.
- Éviter les doublons lors des reprises et distinguer une véritable erreur réseau d’un transfert toujours en cours.
- Afficher un état fiable à l’utilisateur et permettre la reprise des transferts interrompus.
Contraintes : examiner le code existant avant toute modification, réutiliser les mécanismes déjà mis en place pour l’enregistrement en arrière-plan lorsque c’est pertinent, et préserver la file d’attente, la transcription et les autres fonctionnalités.
Résultat attendu : l’utilisateur peut lancer la sauvegarde d’un enregistrement, quitter l’application ou verrouiller son téléphone, puis revenir sans perdre le fichier ni subir une fausse erreur de connexion. Le transfert doit se terminer ou reprendre automatiquement, dans les limites autorisées par Android et iOS.