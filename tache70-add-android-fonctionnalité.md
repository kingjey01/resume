# Fonctionnalité Android : « Payer pour un autre étudiant »

Ajouter une option **« Payer pour un autre »** dans la fenêtre de paiement, aussi bien pour l’achat individuel d’un résumé que pour la souscription à un abonnement QCM.

### 1. Interface de paiement
Ajouter un choix entre :
- **Payer pour moi** : conserver intégralement le fonctionnement actuel.
- **Payer pour un autre** : afficher les champs suivants :
  - **Numéro du payeur** : préremplir avec le numéro associé au compte connecté, mais permettre sa modification afin que le payeur puisse utiliser un autre numéro Mobile Money.
  - **Numéro du bénéficiaire** : saisir le numéro de téléphone associé au compte de l’étudiant qui doit recevoir l’achat ou l’abonnement.

### 2. Validation du bénéficiaire
Avant de lancer le paiement :
- Vérifier que le numéro du bénéficiaire correspond à un compte étudiant existant et actif.
- Refuser le paiement si le compte est inexistant, inactif ou ne correspond pas à un étudiant.
- Afficher clairement l'identité du bénéficiaire identifié avant la confirmation du paiement.

### 3. Traitement du paiement
- Le paiement est effectué avec le numéro Mobile Money du payeur, qu’il soit celui de son compte ou un autre numéro saisi.
- Le compte connecté reste identifié comme **payeur**, indépendamment du numéro Mobile Money utilisé.
- Après confirmation effective du paiement par le fournisseur, attribuer exclusivement l’achat du résumé ou l’abonnement au compte du bénéficiaire.
- Ne jamais créditer simultanément le compte du payeur et celui du bénéficiaire.
- En cas d’échec ou d’annulation, ne pas attribuer l’achat ni l’abonnement.

### 4. Notifications
Après confirmation du paiement :
- Créer la notification dans le système en utilisant l’identifiant du **bénéficiaire**.
- Envoyer la notification push exclusivement au bénéficiaire.
- Le message doit lui indiquer qu’un résumé lui a été acheté ou qu’un abonnement QCM lui a été offert.
- Ne pas créer cette notification au nom du payeur et ne pas envoyer la notification d’attribution au payeur.

### 5. Traçabilité et sécurité
Conserver dans la transaction :
- L’identifiant du compte payeur.
- L’identifiant du compte bénéficiaire.
- Le numéro Mobile Money réellement utilisé pour payer.
- Le numéro de téléphone du bénéficiaire.
- Le type d’opération : achat de résumé ou abonnement QCM.
- Le montant, la référence de transaction et le statut du paiement.

La confirmation doit être vérifiée côté backend à partir du retour du fournisseur Mobile Money. Ne jamais attribuer un achat sur la seule base du retour de l’application Flutter.

### 6. Contraintes
- Fonctionnalité disponible uniquement sur Android.
- Ne pas modifier le parcours de paiement actuel « Payer pour moi ».
- Ne pas introduire de régression dans les achats, abonnements, historiques, notifications ou vérifications d’accès existants.
- Respecter les mécanismes actuels de paiement et les fournisseurs Mobile Money déjà intégrés.
- Éviter les doubles attributions en cas de callbacks répétés ou de nouvelles tentatives de paiement.

**Résultat attendu :** un étudiant connecté peut payer un résumé ou un abonnement pour un autre étudiant, avec son propre numéro ou un autre numéro Mobile Money. Le bénéficiaire reçoit effectivement le droit d’accès et la notification, tandis que le payeur reste uniquement enregistré comme initiateur et financeur de la transaction.


### 7. Exigences obligatoires de développement : sécurité, qualité et performances

Appliquer rigoureusement les bonnes pratiques de développement sur Flutter et Django. Ne pas privilégier une implémentation rapide au détriment de la sécurité, de la stabilité ou de la maintenabilité.

**Sécurité et validation des données**
- Valider et normaliser toutes les entrées utilisateur côté Flutter et obligatoirement côté backend.
- Ne jamais faire confiance aux données transmises par l'application mobile.
- Vérifier les permissions, l'authentification, le statut des comptes et les droits d'accès avant chaque opération sensible.
- Prévenir les injections SQL, les accès non autorisés, les manipulations d'identifiants et les failles de type IDOR.
- Ne jamais exposer de données personnelles ou financières inutiles dans les réponses API ou les journaux.
- Protéger les transactions contre les falsifications, les doublons et les rejeux de requêtes.
- Utiliser des requêtes paramétrées ou l'ORM Django. Ne jamais construire des requêtes SQL par concaténation de chaînes.
- Ne jamais faire confiance au numéro de téléphone fourni pour identifier un bénéficiaire sans vérification réelle en base de données.

**Optimisation et performances**
- Éviter les requêtes SQL inutiles, répétitives ou redondantes, notamment les problèmes N+1.
- Utiliser correctement `select_related`, `prefetch_related`, les annotations et les agrégations lorsque cela est pertinent.
- Limiter les champs récupérés et les données retournées par les API.
- Éviter les boucles qui déclenchent des requêtes individuelles en base de données.
- Ajouter des index uniquement lorsqu'ils sont justifiés par les recherches et les contraintes réelles.
- Éviter les traitements lourds synchrones lorsqu'ils peuvent être exécutés de manière asynchrone.
- Ne pas multiplier inutilement les appels API, les accès à la base de données ou les opérations réseau.
- Optimiser le code sans le rendre inutilement complexe.

**Intégrité et fiabilité des transactions**
- Utiliser les transactions atomiques Django (`transaction.atomic`) pour les opérations qui doivent rester cohérentes.
- Garantir qu'un paiement confirmé ne puisse attribuer qu'une seule fois un achat ou un abonnement.
- Gérer correctement les requêtes simultanées, les callbacks répétés, les délais d'attente et les échecs réseau.
- Vérifier côté serveur le montant, la référence, le statut et la correspondance entre la transaction et l'opération attendue.
- Ne jamais considérer une simple réponse Flutter comme une preuve de paiement.
- Prévoir des mécanismes d'idempotence pour éviter les doubles traitements.

**Architecture et maintenabilité**
- Respecter l'architecture, les conventions et les modèles déjà présents dans le projet.
- Réutiliser les services, fonctions et composants existants lorsqu'ils sont adaptés.
- Éviter la duplication de code, les variables inutiles, les fonctions trop longues et les dépendances superflues.
- Séparer clairement la logique métier, les validations, les accès aux données et la présentation.
- Gérer les erreurs proprement avec des messages compréhensibles pour l'utilisateur, sans exposer les détails techniques internes.
- Ne pas modifier des fonctionnalités sans rapport avec cette demande.

**Vérifications et tests obligatoires**
Avant de terminer :
- Examiner les fichiers existants et comprendre le fonctionnement actuel du paiement.
- Tester les deux parcours : paiement personnel et paiement pour un autre étudiant.
- Tester les numéros invalides, comptes inexistants, comptes inactifs et numéros mal formatés.
- Tester les paiements réussis, échoués, annulés, expirés et les callbacks reçus plusieurs fois.
- Vérifier que seul le bénéficiaire reçoit l'achat, l'abonnement et la notification.
- Vérifier que le payeur n'obtient aucun accès indu.
- Tester les cas de requêtes simultanées et les éventuels problèmes de cohérence des données.
- Vérifier les permissions, les réponses API, les erreurs Flutter et les éventuels effets de bord sur les fonctionnalités existantes.

**Règle fondamentale :** ne pas supposer que les données envoyées par l'utilisateur sont fiables. Toute opération sensible doit être contrôlée côté serveur. Privilégier un code sécurisé, optimisé, lisible, maintenable et compatible avec l'architecture actuelle. Ne pas déclarer le travail terminé sans avoir effectué les vérifications nécessaires et signalé clairement les tests réellement exécutés.