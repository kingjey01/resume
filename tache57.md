Prompt 1 — Modifier le prix minimum des résumés
Dans le backend Django et l’application Flutter, modifier la règle métier concernant le prix des résumés.
- Fixer le prix minimum à 300 FC pour les résumés créés manuellement ou générés à partir d’un enregistrement audio.
- Remplacer partout l’ancienne limite de 3 000 FC par 300 FC, notamment dans les validations backend et frontend.
- Garantir que le backend refuse tout prix positif inférieur à 300 FC, même si une requête contourne les validations Flutter.
- Préserver la possibilité de proposer gratuitement un résumé lorsque le fonctionnement actuel le permet.
- Vérifier qu’aucune ancienne validation ou valeur codée en dur ne conserve le seuil de 3 000 FC.
Ne modifier aucune autre règle métier ni l’interface sans nécessité.
Prompt 2 — Ajouter un quota mensuel de génération de QCM lié à l’abonnement
Mettre en place un système de quotas mensuels de génération de QCM, lié à l’abonnement de chaque étudiant, avec une gestion complète dans Django et Flutter.
1. Gestion du quota
- Chaque abonnement doit comporter une date de début, une date de fin, un quota mensuel de génération de QCM et le nombre de générations déjà consommées.
- plafond journalier pour éviter qu'un compte vide le quota en une heure ;
compteur serveur uniquement, jamais côté application
- Le quota doit être vérifié côté backend avant chaque génération afin d’empêcher tout dépassement, même en cas de requêtes simultanées.
- Le quota doit être réinitialisé à chaque nouvelle période mensuelle de l’abonnement, selon une logique cohérente avec sa durée.
- Lorsqu’un étudiant atteint son quota, bloquer immédiatement toute nouvelle génération de QCM, même si son abonnement est encore valide.
- Un nouvel abonnement doit ouvrir une nouvelle période de consommation selon les règles définies, sans permettre de contourner artificiellement les limites.
- Conserver les limites existantes de 8 questions par niveau sur 3 niveaux, soit 24 questions maximum par résumé. Ce plafond par résumé reste distinct du quota global de l’abonnement.
2. Interface Flutter
Dans la section Exercices, ajouter un troisième onglet intitulé « Quota d’abonnement », à côté des onglets existants de tentatives et de statistiques.
Afficher :
- Le statut de l’abonnement.
- Sa date de début et sa date d’expiration.
- Le quota mensuel total.
- planfond journalier et ce qui reste  du jours courent
- Le nombre de générations consommées et le quota restant.
- La prochaine date de réinitialisation du quota, si applicable.
Lorsque le quota est épuisé, afficher un message explicite et proposer le renouvellement de l’abonnement. Ne pas autoriser la génération tant que les conditions nécessaires ne sont pas remplies.
3. Contraintes techniques
- Examiner le système actuel d’abonnement, de paiement et de génération des QCM avant toute modification.
- Définir clairement ce qui consomme une unité de quota : une génération complète de QCM pour un résumé, et non chaque question individuellement.
- Éviter de décompter plusieurs fois une même génération à cause des nouvelles tentatives réseau.
- Ne pas consommer le quota si la génération échoue avant de produire un résultat exploitable.
- Garantir que les contrôles backend font autorité et que l’interface reflète fidèlement les données du serveur.
- Préserver les achats de résumés, les tentatives, les statistiques et les autres fonctionnalités existantes.
Résultat attendu : chaque étudiant peut générer des QCM dans les limites de son abonnement. Dès que son quota mensuel est épuisé, la génération est bloquée, même si son abonnement n’a pas encore expiré.