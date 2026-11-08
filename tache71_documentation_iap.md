# Tâche 71 — Documentation Apple In-App Purchase

## 1. Architecture finale

```
iOS (StoreKit 2 via in_app_purchase)
   │  achat / restauration
   ▼
Flutter AppleIapService
   │  JWS signé (serverVerificationData)
   ▼
Django POST /api/apple/verify/  ── vérifie la signature Apple
   │                               (SignedDataVerifier + racines Apple G2/G3)
   ├── Purchase (source=apple, transaction_id Apple)
   ├── Abonnement (source=apple, expiration Apple)
   └── AppleTransaction (journal + idempotence)

Apple ── App Store Server Notifications V2 ──▶ POST /api/apple/notifications/
                                                 renouvellement / expiration /
                                                 remboursement / révocation /
                                                 changement de renouvellement

Android ── FlexPay (inchangé, aucun code Apple appelé)
Web     ── FlexPay / comportement actuel (stub Apple)
```

Le backend reste la seule autorité : **aucun droit n'est accordé sur le seul
retour StoreKit**. L'application attend la réponse de `/api/apple/verify/`
avant de compléter l'achat et de rafraîchir l'interface.

## 2. Fichiers créés

Backend :
```
backend/payments/apple_iap.py
backend/payments/apple_views.py
backend/payments/apple_root_certs/AppleRootCA-G2.cer
backend/payments/apple_root_certs/AppleRootCA-G3.cer
backend/payments/migrations/0008_applenotification_abonnement_apple_environment_and_more.py
backend/users/migrations/0013_userprofile_apple_app_account_token.py
backend/payments/tests_apple.py
```

Flutter :
```
lib/services/apple_iap/apple_iap_types.dart
lib/services/apple_iap/apple_iap_service_stub.dart
lib/services/apple_iap/apple_iap_service_io.dart
lib/features/purchases/widgets/apple_purchase_button.dart
```

## 3. Fichiers modifiés

```
backend/payments/models.py
backend/payments/urls.py
backend/payments/views.py (aucun changement fonctionnel Apple, voir apple_views.py)
backend/users/models.py
backend/resume_backend/settings.py
backend/resume_backend/settings_production.py
backend/requirements.txt
backend/.env.example
lib/services/api_service.dart
lib/features/summary_details/screens/summary_details_screen.dart
lib/features/subscriptions/widgets/service_card.dart
lib/features/exercises/screens/exercise_subscription_screen.dart
pubspec.yaml / pubspec.lock
```

Aucun fichier `android/` n'est modifié.

## 4. Dépendances

- Flutter : `in_app_purchase: ^3.3.1` (StoreKit 2 sur iOS, aucun appel sur
  Android/Web grâce aux imports conditionnels).
- Backend : `app-store-server-library==3.1.2` (bibliothèque officielle Apple).

## 5. Modèles de données

- `Service.apple_product_id` : produit d'abonnement Apple du service QCM.
- `Purchase.source`, `apple_transaction_id` (unique), `apple_original_transaction_id`,
  `apple_environment`, `payment_method='apple'`.
- `Abonnement.source`, `apple_original_transaction_id`, `apple_environment`.
- `AppleTransaction` : journal des transactions validées (idempotence).
- `AppleNotification` : journal des notifications Apple (UUID unique).
- `UserProfile.apple_app_account_token` : UUID stable transmis à StoreKit
  (`appAccountToken`) pour rattacher une notification initiale au compte.

## 5 bis. Interface Flutter iOS

- **Résumé** (`summary_details_screen`) : sur iOS, le bouton « Acheter »
  ouvre une fenêtre Apple (jamais FlexPay) ; prix localisé App Store.
- **Abonnement** (`service_card`, écran des abonnements) : sur iOS, la fenêtre
  d'abonnement affiche uniquement le bouton Apple.
- **Abonnement QCM** (`exercise_subscription_screen`) : sur iOS, le champ
  Mobile Money et le bouton FlexPay sont remplacés par le bouton Apple et un
  bouton « Restaurer mes achats ».
- L'achat est complété (`completePurchase`) uniquement après confirmation
  backend ; les providers achats/abonnements sont rafraîchis ensuite.
- Android et Web ne voient aucun de ces éléments : leur parcours reste
  identique à avant.

## 6. Endpoints

| Méthode | URL | Accès | Rôle |
|---|---|---|---|
| GET | `/api/apple/products/` | authentifié | IDs produits, prix, `app_account_token` |
| POST | `/api/apple/verify/` | authentifié | vérifie le JWS et attribue le droit |
| POST | `/api/apple/notifications/` | Apple (sans JWT) | App Store Server Notifications V2 |

`/api/apple/verify/` attend `signed_transaction` (JWS) et, pour un résumé,
`summary_id`. Le produit identifie le service QCM côté serveur.

## 7. Variables d'environnement (noms uniquement)

```
APPLE_BUNDLE_ID=com.kingjey01.resumeplus
APPLE_ISSUER_ID=
APPLE_KEY_ID=
APPLE_PRIVATE_KEY_PATH=
APPLE_ENVIRONMENT=Sandbox   # ou Production sur le serveur de production
APPLE_APP_APPLE_ID=
APPLE_SUMMARY_PRODUCTS={}   # JSON {product_id: prix_cdf}
```

**Aucune valeur secrète ne doit être commitée.** La clé privée Apple (.p8) est
déposée sur le serveur et son chemin est seul référencé.

## 8. Produits Apple attendus

- **Résumés** : produits consommables par palier de prix, ex.
  `com.kingjey01.resumeplus.summary.300`, `...500`, `...1000`.
  À créer dans App Store Connect, puis renseigner `APPLE_SUMMARY_PRODUCTS`
  (`{"product_id": prix_cdf}`).
- **Abonnements QCM** : produits auto-renouvelables, un par service, renseignés
  dans `Service.apple_product_id` (admin Django ou données de seed).

Le code ne suppose aucun identifiant : sans produit configuré, l'interface iOS
affiche « Achats Apple indisponibles pour le moment » et n'utilise jamais
FlexPay sur iOS.

## 9. Procédure Sandbox

1. Créer les produits et abonnements dans App Store Connect (état « Prêt à
   soumettre »).
2. Créer un testeur Sandbox (Utilisateurs et accès → Sandbox).
3. Sur le serveur de test : `APPLE_ENVIRONMENT=Sandbox`, renseigner
   `APPLE_SUMMARY_PRODUCTS`, la clé App Store Server API si utilisée, et les
   `Service.apple_product_id`.
4. Installer une build iOS de test (TestFlight ou Xcode) sur un appareil
   connecté avec le compte Sandbox.
5. Tester : achat résumé, achat abonnement, annulation, restauration,
   renouvellement (accéléré en Sandbox), remboursement.
6. Vérifier côté Django : `Purchase.source='apple'`, `Abonnement.source='apple'`,
   `AppleTransaction`, `AppleNotification`.

## 10. Procédure production

1. Créer la clé App Store Server API (App Store Connect → Utilisateurs et
   accès → Intégrations → Clés) et déposer le `.p8` sur le serveur.
2. Renseigner `APPLE_ISSUER_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY_PATH`,
   `APPLE_BUNDLE_ID`, `APPLE_APP_APPLE_ID`, `APPLE_ENVIRONMENT=Production`.
3. Configurer l'URL des notifications V2 :
   `https://<domaine>/api/apple/notifications/`.
4. Appliquer les migrations :
   `python manage.py migrate`.
5. Redémarrer Gunicorn/Celery.
6. Vérifier `/api/apple/products/` avec un compte authentifié.

## 11. Retour arrière

- Les nouvelles colonnes sont nullables ou ont des valeurs par défaut : aucune
  migration destructive.
- Désactiver côté iOS en laissant `APPLE_SUMMARY_PRODUCTS={}` et en vidant
  `Service.apple_product_id` : l'interface iOS affiche « indisponible » et
  n'appelle ni StoreKit ni FlexPay.
- Les achats FlexPay existants ne sont pas modifiés.
- Ne pas supprimer les lignes `Purchase`/`Abonnement` : les droits existants
  doivent rester valides.

## 12. Tests exécutés

Backend :

```bash
cd backend
PYTHONIOENCODING=utf-8 python manage.py test payments.tests payments.tests_apple \
  --settings=resume_backend.settings_test
```

Résultat : **28 tests OK** (14 tests Apple + 14 tests paiement tâche 70).

Couverts : authentification, configuration produits, achat résumé idempotent,
transaction réutilisée par un autre compte, prix incohérent, produit inconnu,
bundle ID incohérent, signature invalide, abonnement Apple, notification
initiale avec appAccountToken, notification dupliquée, renouvellement,
expiration, remboursement.

Compilation :
- `flutter build web --release --base-href=/` : OK (stub Web, aucune dépendance
  StoreKit compilée pour le Web) ;
- `flutter build appbundle --release` : **OK**, `app-release.aab` 69,9 Mo,
  signature vérifiée (`jar verified`) ;
- `flutter analyze` : aucune erreur sur les fichiers Apple IAP ;
- aucun fichier `android/` modifié.

**Incident de build release (préexistant, sans rapport avec IAP)** :
`integration_test`, dépendance de test, était présent dans
`GeneratedPluginRegistrant.java` et absent du classpath release, ce qui faisait
échouer `bundleRelease`. L'AAB a été produit en retirant temporairement
`integration_test` du graphe release, puis `pubspec.yaml` et le registrant ont
été restaurés. Pour que les prochains builds release fonctionnent sans
contournement, activer le **Mode développeur Windows** (obligatoire pour les
liens symboliques des plugins Flutter) ou exclure `integration_test` du graphe
release.

**Non testé ici** : achats réels Sandbox/TestFlight (nécessitent les produits
App Store Connect et un appareil iOS), restauration réelle, notifications Apple
réelles. Les tests backend utilisent un vérificateur mocké.

## 13. Actions propriétaire App Store Connect

1. **Produits consommables de résumé** : App Store Connect → Mon app →
   Achats intégrés → « + » → Consommable. Pour chaque palier : référence
   interne, ID produit (`com.kingjey01.resumeplus.summary.<prix>`), prix,
   territoires, nom/localisation, capture de revue.
2. **Abonnements QCM** : Abonnements → groupe « QCM Muhtasari+ » → créer un
   abonnement auto-renouvelable par plan, avec durée, prix, essai éventuel,
   captures de revue. Renseigner l'ID produit dans `Service.apple_product_id`.
3. **Clé App Store Server API** : Utilisateurs et accès → Intégrations →
   App Store Server API → générer une clé, télécharger le `.p8` une seule fois,
   noter Key ID et Issuer ID. Déposer le fichier sur le serveur (jamais Git).
4. **Notifications V2** : App Store Connect → Mon app → Informations de l'app
   → Notifications de serveur → URL
   `https://<domaine>/api/apple/notifications/`, version V2.
5. **Accords/fiscalité/banque** : contrats payants, coordonnées bancaires et
   fiscales à jour.
6. **Testeurs Sandbox** : Utilisateurs et accès → Sandbox → créer un testeur.
7. **TestFlight** : créer une build, la distribuer aux testeurs, tester les
   achats Sandbox.

Ne jamais communiquer les valeurs de `APPLE_PRIVATE_KEY_PATH`, du contenu du
`.p8`, de l'Issuer ID ou du Key ID dans une conversation ou un dépôt.
