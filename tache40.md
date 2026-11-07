Permettre l’enregistrement audio et l’envoi au serveur en arrière-plan
Analyse et corrige le fonctionnement de l’enregistrement audio et de l’envoi des fichiers audio vers le serveur dans l’application Flutter.
Problème constaté : lorsqu’un utilisateur enregistre une session audio ou envoie un enregistrement vers le serveur, l’opération se bloque dès qu’il quitte l’application, la met en arrière-plan ou verrouille son téléphone. Actuellement, l’utilisateur doit maintenir l’application ouverte au premier plan pendant toute l’opération.
Objectifs :
1. Permettre à l’enregistrement audio de continuer lorsque l’application passe en arrière-plan, lorsque l’utilisateur ouvre une autre application ou lorsque le téléphone est verrouillé.
2. Permettre l’envoi des fichiers audio vers le serveur de continuer en arrière-plan, même lorsque l’utilisateur quitte l’application ou verrouille son téléphone.
3. Garantir la continuité des opérations pour les enregistrements de longue durée, dans la limite des capacités autorisées par Android et iOS.
4. Assurer la persistance de l’enregistrement local et de son état d’envoi afin qu’une interruption de l’application ou du réseau ne provoque pas la perte du fichier.
5. Prévoir la reprise des envois interrompus, avec une gestion correcte des erreurs et des tentatives de reconnexion, sans créer de doublons sur le serveur.
6. Afficher correctement l’état de l’opération : enregistrement en cours, envoi en arrière-plan, progression, échec ou réussite.
7. Examiner les différences entre Android et iOS et implémenter les mécanismes adaptés à chaque plateforme, notamment les autorisations, les services d’arrière-plan et les restrictions du système.
Contraintes importantes :
- Examiner d’abord l’architecture actuelle de l’enregistrement audio, de la gestion des fichiers locaux et de l’upload.
- Identifier précisément les causes des blocages avant de modifier le code.
- Ne pas confondre la continuité de l’enregistrement audio avec celle de l’envoi au serveur : ce sont deux opérations distinctes qui doivent être gérées correctement.
- Respecter les limites des systèmes d’exploitation : ne pas promettre un fonctionnement en arrière-plan que la plateforme ne permet pas.
- Ne pas modifier les règles métier, le processus de transcription, la file d’attente ou l’interface existante sans nécessité.
- Éviter toute régression dans l’enregistrement au premier plan, la sauvegarde locale et l’envoi actuel.
Résultat attendu : l’utilisateur doit pouvoir lancer un enregistrement, quitter l’application ou verrouiller son téléphone, puis revenir constater que l’enregistrement s’est poursuivi normalement. De même, il doit pouvoir lancer l’envoi d’un fichier audio et quitter l’application sans que l’upload dépende du maintien de celle-ci au premier plan.