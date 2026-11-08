# MISSION : INTÉGRATION COMPLÈTE D'APPLE IN-APP PURCHASE DANS MUHTASARI+

## 1. CONTEXTE DU PROJET

L'application Muhtasari+ est développée avec Flutter pour le frontend mobile et Django pour le backend API.

L'application permet notamment :
- La consultation de résumés de cours.
- L'achat de résumés.
- L'accès aux contenus pédagogiques.
- L'utilisation des QCM.
- La souscription à des abonnements donnant accès aux fonctionnalités premium.

Le système de paiement actuel utilise FlexPay.

FlexPay fonctionne actuellement sur Android et doit continuer à fonctionner exactement comme avant.

Une première soumission iOS a été rejetée en raison du système de paiement externe utilisé pour des fonctionnalités numériques.

Nous souhaitons donc intégrer Apple In-App Purchase (IAP), conformément aux règles applicables de l'App Store.

## 2. OBJECTIF PRINCIPAL

Mettre en place un système de paiement Apple natif et sécurisé pour iOS, utilisant StoreKit à travers Flutter In-App Purchase.

L'architecture doit permettre :

- Android : conservation de FlexPay.
- iOS : utilisation d'Apple In-App Purchase.
- Backend Django : validation centralisée des transactions et gestion des droits.
- Synchronisation des achats et abonnements avec le compte utilisateur.

L'intégration doit être propre, évolutive, sécurisée et compatible avec l'architecture existante.

## 3. RÈGLE ABSOLUE : NE PAS CASSER ANDROID

C'est une contrainte prioritaire.

Ne jamais modifier le fonctionnement actuel de FlexPay sur Android.

Ne pas modifier inutilement :
- Les fichiers de configuration Android.
- Les identifiants de l'application Android.
- Les signatures.
- Les paramètres Gradle.
- Les mécanismes de paiement Android.
- Les écrans Android qui fonctionnent déjà.

Toute modification Flutter commune doit être conditionnée par la plateforme lorsque cela est nécessaire.

Avant toute modification, identifier les dépendances entre les fonctionnalités Android et iOS.

Effectuer des tests de non-régression Android après l'intégration.

Ne jamais remplacer FlexPay par Apple IAP globalement.

## 4. PHASE 1 — AUDIT COMPLET AVANT MODIFICATION

Commencer par examiner l'ensemble du système de paiement existant.

### Flutter
Identifier :
- Les écrans d'achat.
- Les services de paiement.
- Les modèles de produits.
- Les appels API.
- Les mécanismes de confirmation.
- La gestion des erreurs.
- Les pages d'abonnement.
- Les états de chargement.
- Les éventuels mécanismes de restauration des achats.

### Django
Identifier :
- Les modèles Purchase.
- Les modèles Subscription.
- Les modèles UserDevice ou équivalents.
- Les vues API de paiement.
- Les serializers.
- Les services de validation.
- Les permissions.
- Les tâches Celery éventuelles.
- Les mécanismes d'attribution et de révocation des droits.

### Livrable obligatoire
Produire un rapport présentant :
1. L'architecture actuelle.
2. Les fichiers concernés.
3. Les points de modification nécessaires.
4. Les risques de régression.
5. Les éventuelles incompatibilités.
6. Le plan d'intégration proposé.

Ne commencer les modifications qu'après avoir établi cette architecture.

## 5. PHASE 2 — INTÉGRATION FLUTTER

Utiliser le package officiel Flutter In-App Purchase, dans une version compatible avec le projet.

Documentation de référence :
https://pub.dev/packages/in_app_purchase

Mettre en place un service de paiement Apple indépendant du service FlexPay.

Exemple d'organisation indicative :
- AppleIapService.
- ApplePurchaseRepository.
- ApplePurchaseController.

Adapter les noms à l'architecture réelle du projet.

### Fonctionnalités nécessaires

1. Récupération des produits disponibles dans l'App Store.
2. Affichage des prix retournés par Apple.
3. Lancement d'un achat.
4. Gestion des achats en attente.
5. Gestion des achats réussis.
6. Gestion des achats annulés.
7. Gestion des erreurs.
8. Transmission des informations de transaction au backend Django.
9. Attente de la confirmation du backend avant d'accorder les droits.
10. Restauration des achats lorsque cela est applicable.

Ne jamais considérer un achat comme valide uniquement parce que StoreKit retourne un succès.

Le backend doit confirmer la transaction avant que l'application attribue les droits.

### Gestion des plateformes

- Android : conserver le flux FlexPay existant.
- iOS : utiliser Apple In-App Purchase.
- Web : ne pas modifier le comportement actuel sans nécessité.

Isoler les opérations par plateforme.

## 6. PHASE 3 — ORGANISATION DES PRODUITS APPLE

Préparer le code pour prendre en charge les types de produits suivants :

### A. Achat individuel de résumés

Les résumés peuvent être achetés individuellement.

Étudier le modèle de produit Apple le plus adapté.

Si les contenus achetés doivent rester accessibles au compte utilisateur, prévoir une gestion cohérente de leur restauration et de leurs droits.

Ne pas utiliser un abonnement pour un achat qui doit être définitif.

### B. Abonnements QCM

Prévoir des abonnements renouvelables automatiquement.

Le code doit gérer :
- Abonnement actif.
- Renouvellement.
- Expiration.
- Annulation du renouvellement.
- Période de grâce éventuelle.
- Remboursement.
- Révocation.

Les identifiants des produits Apple doivent être centralisés dans une configuration propre, sans être dispersés dans les écrans.

Ne pas inventer les identifiants définitifs : ils seront communiqués après leur création dans App Store Connect.

## 7. PHASE 4 — BACKEND DJANGO

Créer un système de validation des achats Apple côté serveur.

Le backend doit rester l'autorité centrale pour l'attribution des droits.

### A. Endpoint de validation

Créer un endpoint sécurisé permettant à Flutter de transmettre une transaction Apple.

Le format doit utiliser les données de transaction nécessaires à la validation moderne d'Apple.

Privilégier l'utilisation de l'App Store Server API et des données signées Apple.

Ne pas faire confiance à un simple identifiant produit transmis par le client.

### B. Vérifications obligatoires

Le backend doit vérifier :

- L'authenticité de la transaction.
- L'identifiant du produit.
- Le bundle ID de l'application.
- L'environnement de transaction.
- L'identifiant de transaction.
- L'identifiant de transaction d'origine.
- Le statut de l'achat.
- La date d'expiration pour les abonnements.
- L'absence de réutilisation frauduleuse d'une transaction.
- La correspondance avec le compte utilisateur.

Utiliser les bibliothèques et mécanismes de vérification cryptographique officiellement recommandés par Apple.

Ne jamais accepter une transaction simplement parce que l'application mobile affirme qu'elle est valide.

### C. Idempotence

La validation doit être idempotente.

Une même transaction ne doit jamais créer plusieurs achats ou attribuer plusieurs fois les mêmes droits.

Prévoir des contraintes d'unicité adaptées aux identifiants de transaction Apple.

Gérer correctement les appels répétés après une interruption réseau.

### D. Historique

Enregistrer les informations utiles :
- Utilisateur.
- Produit.
- Identifiant de transaction.
- Transaction d'origine.
- Date d'achat.
- Date d'expiration.
- Environnement.
- Statut.
- Type de produit.

Ne jamais enregistrer inutilement des informations sensibles.

## 8. PHASE 5 — NOTIFICATIONS SERVEUR APPLE

Prévoir l'intégration des App Store Server Notifications V2.

Créer un endpoint spécifique pour recevoir les notifications Apple.

Gérer notamment :
- Achat initial.
- Renouvellement.
- Expiration.
- Résiliation.
- Remboursement.
- Révocation.
- Modification de l'état d'un abonnement.

Vérifier cryptographiquement les données signées reçues.

Ne jamais faire confiance à une notification sans validation.

Prévoir :
- La gestion des notifications répétées.
- L'idempotence.
- Les erreurs temporaires.
- Les journaux techniques.
- Le traitement asynchrone si nécessaire.

La réception d'une notification ne doit jamais provoquer une attribution incorrecte des droits.

## 9. PHASE 6 — SYNCHRONISATION DES DROITS

Les droits doivent être centralisés dans Django.

Un utilisateur qui possède déjà des résumés ou un abonnement valide doit retrouver ses droits lorsqu'il se connecte sur iOS avec le même compte.

Ne pas créer deux systèmes de droits indépendants.

Attention :
- Un achat Apple ne doit pas être automatiquement considéré comme un paiement FlexPay.
- Un paiement FlexPay ne doit pas être présenté comme une transaction Apple.
- Les sources de paiement doivent être identifiables.
- Les droits existants doivent être conservés.
- Les règles d'accès doivent être cohérentes entre plateformes.

Prévoir une gestion correcte des remboursements et révocations sans supprimer les achats indépendants toujours valides.

## 10. PHASE 7 — RESTAURATION DES ACHATS

Implémenter une fonction permettant à l'utilisateur de restaurer ses achats Apple lorsque cela est applicable.

Après restauration :
1. Récupérer les transactions disponibles.
2. Transmettre les informations nécessaires au backend.
3. Vérifier les transactions.
4. Associer les droits au compte authentifié.
5. Actualiser l'interface.

Ne jamais attribuer les droits à un utilisateur non authentifié.

Prévoir les cas où l'utilisateur a acheté avec un compte Apple différent de celui utilisé dans l'application.

## 11. PHASE 8 — SÉCURITÉ OBLIGATOIRE

Appliquer les règles suivantes sur l'ensemble du code :

- Validation stricte de toutes les entrées utilisateur.
- Authentification obligatoire des endpoints concernés.
- Permissions Django adaptées.
- Protection contre les attaques par rejeu.
- Protection contre les doublons de transaction.
- Validation cryptographique des données Apple.
- Gestion sécurisée des erreurs.
- Absence d'informations sensibles dans les logs.
- Pas de confiance accordée aux montants transmis par Flutter.
- Pas de confiance accordée aux identifiants produit non vérifiés.
- Transactions de base de données atomiques lorsque nécessaire.
- Requêtes ORM optimisées.
- Index et contraintes d'unicité adaptés.
- Pas de secrets dans le code source.
- Pas de clés privées dans Flutter.
- Pas de certificats privés dans le dépôt Git.

Utiliser les variables d'environnement pour les secrets.

Ne jamais afficher une clé API, un mot de passe, un token, un certificat privé ou une information personnelle dans les fichiers de documentation, les rapports, les captures d'écran ou les journaux.

Si une information confidentielle est nécessaire, indiquer uniquement le nom de la variable d'environnement attendue.

Exemple :
APPLE_PRIVATE_KEY_PATH
APPLE_ISSUER_ID
APPLE_KEY_ID

Ne jamais inscrire leurs valeurs réelles dans le code ou les livrables.

## 12. PHASE 9 — TESTS

Prévoir des tests automatisés pour :

### Flutter
- Chargement des produits.
- Achat réussi.
- Achat annulé.
- Achat en attente.
- Erreur réseau.
- Transaction déjà traitée.
- Restauration.
- Échec de validation backend.

### Django
- Transaction valide.
- Transaction invalide.
- Mauvais Bundle ID.
- Mauvais produit.
- Transaction déjà utilisée.
- Utilisateur non authentifié.
- Notification Apple invalide.
- Renouvellement.
- Expiration.
- Remboursement.
- Révocation.
- Répétition d'une notification.

### Non-régression
Tester impérativement :
- Connexion Android.
- Achat Android via FlexPay.
- Validation FlexPay.
- Attribution des droits.
- Consultation des résumés.
- Abonnement QCM.
- Connexion iOS.
- Achat Apple.
- Synchronisation des droits entre plateformes.

Ne pas déclarer l'intégration terminée sans résultats de tests documentés.

## 13. PHASE 10 — DOCUMENTATION ET DÉPLOIEMENT

Créer une documentation technique contenant :

- Architecture finale.
- Liste des fichiers créés.
- Liste des fichiers modifiés.
- Dépendances ajoutées.
- Variables d'environnement nécessaires, sans leurs valeurs.
- Endpoints créés.
- Identifiants de produits attendus.
- Configuration App Store Server API.
- Configuration App Store Server Notifications V2.
- Procédure de test Sandbox.
- Procédure de production.
- Procédure de retour arrière.

Ne pas effectuer de déploiement en production sans autorisation explicite.

Ne pas effectuer de migration destructive.

Ne pas supprimer les anciennes données d'achat.

Ne pas modifier les paramètres de production Android.

## 14. PHASE 11 — PRÉPARATION APP STORE CONNECT

Produire une liste précise de toutes les opérations que le propriétaire du compte devra effectuer manuellement :

- Création des produits d'achat individuel.
- Création des abonnements QCM.
- Configuration des groupes d'abonnements.
- Configuration des prix et territoires.
- Configuration des informations de revue.
- Configuration de la clé App Store Server API.
- Configuration des notifications serveur.
- Acceptation éventuelle des accords Apple.
- Configuration des informations fiscales et bancaires si nécessaire.
- Création des utilisateurs Sandbox.
- Préparation des tests TestFlight.

Pour chaque opération, fournir :
1. Le menu exact à ouvrir.
2. Le champ à renseigner.
3. La valeur attendue ou le format attendu.
4. Les informations que le développeur doit fournir.
5. Les éventuelles captures d'écran nécessaires.

Ne jamais demander au propriétaire de publier des secrets dans une conversation ou un dépôt Git.

## 15. RÈGLE DE TRAVAIL

Procéder par étapes.

Ne pas modifier tout le projet en une seule fois.

Pour chaque phase :
1. Examiner l'existant.
2. Présenter les fichiers concernés.
3. Expliquer les modifications.
4. Implémenter proprement.
5. Exécuter les tests.
6. Présenter les résultats.
7. Signaler les opérations qui nécessitent l'intervention du propriétaire.

Si un point est incertain, poser une question avant de prendre une décision risquée.

Ne jamais inventer une configuration Apple.

Ne jamais supposer qu'un produit existe déjà dans App Store Connect.

Ne jamais remplacer une fonctionnalité existante sans vérifier ses dépendances.

## 16. LIVRABLE FINAL

À la fin, fournir :

- Un système Apple IAP opérationnel.
- Un backend Django sécurisé.
- Une intégration Flutter iOS.
- Une conservation intégrale du paiement Android FlexPay.
- La gestion des achats et abonnements.
- La restauration des achats.
- Les notifications serveur Apple.
- Les tests automatisés.
- Un rapport de non-régression Android.
- Une documentation de déploiement.
- Une liste des actions restantes dans App Store Connect.

IMPORTANT : commencer par la PHASE 1, l'audit. Ne pas commencer directement à modifier le code.