# Tâche 71 — Audit avant intégration Apple In-App Purchase

Date : 2026-11-08
Bundle iOS constaté : **`com.kingjey01.resumeplus`** (source :
`ios/Runner.xcodeproj/project.pbxproj`).

## 1. Architecture de paiement actuelle

### Flutter

| Élément | Fichier |
|---|---|
| Écrans d'achat de résumé | `lib/features/summary_details/screens/summary_details_screen.dart`, `lib/features/purchases/screens/purchase_summary_screen.dart` |
| Écrans d'abonnement | `lib/features/subscriptions/widgets/service_card.dart`, `lib/features/exercises/screens/exercise_subscription_screen.dart` |
| Suivi du paiement | `lib/features/purchases/screens/payment_status_screen.dart` (polling `/purchases/check-status/<ref>/`) |
| Appels API | `lib/services/api_service.dart` (`initiateSummaryPurchase`, `initiateSubscriptionPayment`, `createSubscriptionAfterPayment`) |
| Modèles | `lib/models/summary.dart`, `lib/models/service.dart`, `lib/models/abonnement.dart` |
| Fonctionnalité tâche 70 | `lib/features/purchases/widgets/payment_recipient_selector.dart` |

- Paiement actuel : **FlexPay uniquement** (Mobile Money), sur Android et iOS.
- Aucun package `in_app_purchase` ni code StoreKit.
- Aucun mécanisme de restauration d'achats.
- Les écrans sont partagés Android/iOS : toute branche iOS doit être isolée par
  plateforme.
- L'application a aussi une cible Web/PWA : les imports IAP doivent être
  conditionnels pour ne pas casser `flutter build web`.

### Django

| Élément | Fichier |
|---|---|
| Modèles | `backend/payments/models.py` — `Service`, `Purchase`, `Abonnement` |
| Initiation / callback FlexPay | `backend/payments/flexpay_integration.py` |
| Vues et statuts | `backend/payments/views.py` |
| Routes | `backend/payments/urls.py`, inclus sous `/api/` |
| Notifications | `backend/notifications/tasks.py` + signaux `backend/payments/signals.py` |
| Droits | `Purchase` (résumé) et `Abonnement` (QCM), lus par les vues d'accès et les providers Flutter |

- `Purchase` ne distingue pas la source du paiement.
- Aucune table de transaction Apple, aucun identifiant de transaction Apple.
- Aucun endpoint de validation Apple, aucune notification serveur Apple.
- Le backend est déjà l'autorité des droits (les vues vérifient `Purchase` et
  `Abonnement`) ; l'IAP doit s'y brancher sans créer un second système.

## 2. Points de modification nécessaires

### Backend

1. `Service.apple_product_id` : mapping produit Apple → service QCM.
2. `Purchase` : `source` (`flexpay`/`apple`), `apple_transaction_id`,
   `apple_original_transaction_id`, `apple_environment`.
3. `Abonnement` : `source`, `apple_original_transaction_id`,
   `apple_environment`.
4. Nouvelle table `AppleTransaction` (journal + idempotence) : utilisateur,
   produit, transaction, transaction d'origine, dates, environnement, statut.
5. Nouvelle table `AppleNotification` : UUID de notification unique, type,
   sous-type, transaction, statut de traitement (idempotence des notifications).
6. Module `payments/apple_iap.py` utilisant la bibliothèque officielle
   `app-store-server-library` (installée) :
   - `SignedDataVerifier` pour les JWS signés Apple (transactions et
     notifications) avec les certificats racines Apple G2/G3 ;
   - `AppStoreServerAPIClient` pour récupérer une transaction à partir de son
     identifiant si nécessaire.
7. Endpoints :
   - `GET /api/apple/products/` : mapping public des identifiants produits
     (résumés par palier de prix, abonnements par service), pour éviter de
     coder les IDs dans Flutter ;
   - `POST /api/apple/verify/` (authentifié) : valide une transaction signée,
     attribue l'achat/abonnement au compte connecté, idempotent ;
   - `POST /api/apple/notifications/` (non authentifié, Apple) : vérifie
     `signedPayload`, traite renouvellements, expirations, remboursements,
     révocations, idempotent.
8. Configuration (noms de variables uniquement, aucune valeur) :
   `APPLE_BUNDLE_ID`, `APPLE_ISSUER_ID`, `APPLE_KEY_ID`,
   `APPLE_PRIVATE_KEY_PATH`, `APPLE_ENVIRONMENT`, `APPLE_APP_APPLE_ID`,
   `APPLE_SUMMARY_PRODUCTS` (JSON produit → prix CDF).
9. Tests unitaires avec vérificateur mocké (aucun appel Apple réel).

### Flutter

1. Ajouter `in_app_purchase` (dernière version compatible).
2. Service iOS isolé, avec import conditionnel Web :
   - récupération des produits via `/api/apple/products/` ;
   - achat, achat en attente, annulation, erreur ;
   - envoi du JWS (`serverVerificationData`) à `/api/apple/verify/` ;
   - attente de la confirmation backend avant d'accorder les droits ;
   - restauration des abonnements ;
   - rafraîchissement des providers achats/abonnements.
3. UI iOS : remplacer le formulaire FlexPay par un bouton Apple sur iOS
   uniquement (Android/Web inchangés). Si les produits ne sont pas configurés,
   afficher clairement « achats indisponibles » au lieu de retomber sur
   FlexPay.
4. Bouton « Restaurer mes achats » visible sur iOS.
5. Aucune modification des écrans Android ni du parcours FlexPay.

## 3. Modèle de produits Apple proposé

### Résumés (achat définitif)

Les résumés ont des **prix dynamiques**. Apple impose un prix fixe par produit
IAP. La seule solution scalable est un **produit consommable par palier de
prix** :

```json
{
  "com.kingjey01.resumeplus.summary.300": {
    "summary_price_cdf": 300,
    "apple_price": "0.99",
    "currency": "USD"
  }
}
```

- Flutter choisit le produit correspondant au prix du résumé.
- Le backend vérifie que le prix du résumé correspond à `summary_price_cdf`
  **et** que le montant/devise de la transaction signée Apple correspond à
  `apple_price`/`currency`. Aucune conversion automatique 300 CDF ↔ 0,99 USD
  n'est supposée : l'équivalence est déclarée explicitement.
- L'achat est **consommable** (pas d'abonnement) ; la restauration StoreKit ne
  s'applique pas aux consommables, mais le droit reste attaché au compte Django
  et est retrouvé à la connexion sur iOS. C'est le comportement attendu pour un
  contenu acheté définitif.
- Un produit non consommable par résumé serait ingérable (un produit par
  résumé). Cette solution est donc écartée.

### Abonnements QCM

- **Abonnement auto-renouvelable** Apple, un produit par service
  (`Service.apple_product_id`), dans un groupe d'abonnements QCM.
- Le backend reçoit la transaction signée, vérifie l'expiration, crée ou
  prolonge `Abonnement` avec `source='apple'`.
- Les notifications serveur Apple gèrent renouvellement, expiration,
  annulation, période de grâce, remboursement et révocation.

## 4. Risques et incompatibilités

| Risque | Mitigation |
|---|---|
| Casser Android | Aucune modification des fichiers `android/` ; code IAP isolé par `Platform.isIOS` ; tests de non-régression Android |
| Casser le build Web | Imports conditionnels ; stub Web |
| Produits Apple absents | IDs configurables, endpoint de config ; message clair si non configuré |
| Validation client non fiable | JWS vérifié côté serveur avec certificats Apple ; jamais de confiance au seul retour StoreKit |
| Double attribution | Contrainte unique sur `AppleTransaction.transaction_id` + `select_for_update` |
| Notifications répétées | `AppleNotification.notification_uuid` unique + états idempotents |
| Remboursement d'un achat de résumé | Marquer `Purchase.status='refunded'` ; ne pas toucher aux autres achats |
| Restauration sur un autre compte Apple | La transaction signée contient l'identifiant de transaction ; le backend l'attribue au compte authentifié après vérification. Un achat déjà associé à un autre compte est refusé (journal AppleTransaction). |
| Environnements Sandbox/Production | `APPLE_ENVIRONMENT` ; refus des transactions Sandbox en production |

## 5. Plan d'intégration (étapes)

1. **Backend** : modèles + migration, module de vérification, endpoints,
   configuration, tests avec mocks.
2. **Flutter** : dépendance, service IAP iOS, intégration UI iOS, restauration.
3. **Tests** : unités backend (validation, idempotence, notifications),
   compilation Android/Web, tests manuels Sandbox.
4. **Documentation** : procédure Sandbox/production, variables d'environnement,
   actions App Store Connect.

## 6. Actions propriétaire (App Store Connect / Apple)

1. Créer les produits consommables de résumé par palier de prix.
2. Créer les abonnements auto-renouvelables QCM, dans un groupe.
3. Renseigner prix, territoires, traductions, captures de revue.
4. Créer la clé App Store Server API (fichier `.p8`, Key ID, Issuer ID) et la
   déposer sur le serveur (jamais dans Git).
5. Configurer l'URL des App Store Server Notifications V2.
6. Accepter les accords Apple, configurer fiscalité/banque.
7. Créer des testeurs Sandbox et tester via TestFlight.

## 7. Décisions à valider avant les modifications

1. **Modèle résumé** : produit consommable par palier de prix (proposé) —
   confirmer.
2. **Liste des paliers de prix** des résumés (ex. 300, 500, 1000 CDF) — à
   fournir.
3. **Identifiants produits** : seront communiqués après création App Store
   Connect ; le code les lira en configuration.
4. **Restriction iOS** : remplacer FlexPay par IAP sur iOS uniquement
   (recommandé par Apple) — confirmer.
