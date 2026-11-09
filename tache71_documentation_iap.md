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
| GET | `/api/apple/products/` | public | IDs produits, prix, `app_account_token` du compte si authentifié |
| POST | `/api/apple/verify/` | authentifié | vérifie le JWS et attribue le droit |
| POST | `/api/apple/notifications/` | Apple (sans JWT) | App Store Server Notifications V2 |

`/api/apple/products/` est public par conception : il n'expose que les
identifiants produits et les prix App Store (informations publiques), sans
secret ni donnée personnelle. Le jeton `app_account_token` n'est renseigné que
pour un appelant authentifié, sinon `null`.

`/api/apple/verify/` attend `signed_transaction` (JWS) et, pour un résumé,
`summary_id`. Le produit identifie le service QCM côté serveur.

## 7. Variables d'environnement (noms uniquement)

```
APPLE_BUNDLE_ID=com.kingjey01.resumeplus
APPLE_ISSUER_ID=
APPLE_KEY_ID=
APPLE_PRIVATE_KEY_PATH=
APPLE_ENVIRONMENT=Sandbox   # ou Production sur le serveur de production
# Optionnel : Sandbox,Production si les deux doivent être acceptés.
APPLE_ALLOWED_ENVIRONMENTS=
APPLE_APP_APPLE_ID=
# JSON produit -> {summary_price_cdf, apple_price, currency}
APPLE_SUMMARY_PRODUCTS={}
```

Configuration distincte recommandée :

| Contexte | `APPLE_ENVIRONMENT` | `APPLE_ALLOWED_ENVIRONMENTS` |
|---|---|---|
| Test / revue Apple | `Sandbox` | `Sandbox` |
| Production | `Production` | `Production` |
| Revue d'une build App Store nécessitant Sandbox + Production | `Sandbox` | `Sandbox,Production` |

**Aucune valeur secrète ne doit être commitée.** La clé privée Apple (.p8) est
déposée sur le serveur et son chemin est seul référencé.

## 8. Produits Apple attendus

- **Résumés** : produits consommables par palier de prix, ex.
  `com.kingjey01.resumeplus.summary.300`, `...500`, `...1000`.
  À créer dans App Store Connect, puis renseigner `APPLE_SUMMARY_PRODUCTS` au
  format **explicite** :
  ```json
  {
    "com.kingjey01.resumeplus.summary.300": {
      "summary_price_cdf": 300,
      "apple_price": "0.99",
      "currency": "USD"
    }
  }
  ```
  Le prix Apple et le prix Django sont déclarés séparément : **aucune
  conversion automatique** 300 CDF ↔ 0,99 USD n'est supposée. Le backend
  vérifie que le montant et la devise de la transaction signée correspondent
  à `apple_price`/`currency`.
- **Abonnements QCM** : produits auto-renouvelables, un par service, renseignés
  dans `Service.apple_product_id`, avec `Service.apple_price` et
  `Service.apple_currency` déclarés explicitement. Le backend contrôle le
  montant Apple de la transaction.

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
5. Préremplir les données de déploiement (sans utilisateur ni donnée de test) :
   ```bash
   python manage.py seed_deployment \
     --qcm-product-id <produit Apple QCM> \
     --summary-product <produit résumé 300>=300 \
     --summary-product <produit résumé 500>=500
   ```
   La commande est idempotente, ne supprime rien et n'invente aucun identifiant
   Apple. Elle affiche la ligne `APPLE_SUMMARY_PRODUCTS` à ajouter au `.env`.
   Options utiles : `--with-legacy-plans`, `--update-existing`, `--dry-run`,
   `--skip-reference`.
6. Redémarrer Gunicorn/Celery.
7. Vérifier `/api/apple/products/` avec un compte authentifié.

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

Résultat : **41 tests backend OK** (23 tests Apple IAP + 14 tests paiement
tâche 70 + 4 tests du seed de déploiement) et **19 tests Flutter OK**
(`test/apple_iap_pending_summary_test.dart`).

Couverts côté Flutter : purchaseID identique accepté, purchaseID différent
refusé, annulation avec identifiant correspondant (libération) ou différent
(conservation), pending/erreur réseau sans suppression, échec
`completePurchase` (droit et réservation conservés), arrêt après
`completePurchase` avant `clear` (purge au redémarrage), plusieurs
transactions pour un même produit (aucune attribution croisée), transaction
restaurée sans purchaseID (aucun rattachement), réservation ancienne toujours
active, transaction antérieure à la réservation refusée, second achat refusé
quand une transaction est déjà liée, identifiants refusés conservés pour
investigation, état d'interface « finalisation en attente ».

Couverts : authentification, configuration produits, achat résumé idempotent,
transaction réutilisée par un autre compte, prix CDF incohérent, montant Apple
incohérent (0,99 USD), devise Apple incohérente, produit inconnu, bundle ID
incohérent, signature invalide, abonnement Apple, prix Apple d'abonnement
incohérent, notification initiale avec appAccountToken, notification dupliquée,
renouvellement, expiration, remboursement. Les tests vérifient aussi qu'un
remboursement/expiration Apple ne touche pas un achat ou abonnement FlexPay
indépendant.

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

## 12 bis. Corrections issues de l'audit (tâche 72)

- **Liaison transaction ↔ compte** : `process_transaction()` compare
  `payload.appAccountToken` au `UserProfile.apple_app_account_token` de
  l'utilisateur authentifié. Transaction sans jeton, profil sans jeton ou
  jetons différents → `403`. Les transactions déjà enregistrées restent
  idempotentes (retour avant contrôle). Les notifications vérifient aussi la
  cohérence quand les deux jetons sont présents ; sinon elles restent liées
  par `original_transaction_id`.
- **Flutter** : `buySummary()` et `buySubscription()` exigent une session
  authentifiée, un catalogue chargé et un `app_account_token` UUID valide.
  Sinon StoreKit n'est pas appelé et un message invite à se reconnecter.
- **Achats simultanés de résumés** : `PendingSummaryStore` réserve le
  `summary_id` par produit, refuse d'écraser une réservation pour un autre
  résumé, refuse tout nouvel achat dès qu'un `purchaseID` est lié à la
  réservation, survit à un redémarrage et migre l'ancien format. Aucune purge
  temporelle : une réservation ne disparaît qu'après une finalisation
  confirmée ou une annulation dont le `purchaseID` correspond.
- **Transactions incohérentes** : un `purchaseID` différent de celui de la
  réservation, ou une transaction antérieure à la réservation, est refusé et
  n'obtient aucun droit. Son identifiant est conservé dans la réservation
  (`rejected_purchase_ids`, borné) pour investigation, sans jamais changer le
  `summary_id` ni le `purchaseID` d'origine.
- **Restauration sans purchaseID** : aucun rattachement au `summary_id` sur la
  seule base du `productId` ; le message invite à contacter le support.
- **Réconciliation au démarrage** : seules les réservations dont
  `completePurchase` a confirmé la réussite (`status=completed`) sont purgées.
  Une réservation `backend_confirmed` (droit accordé, fin StoreKit inconnue)
  n'est jamais supprimée ; StoreKit redélivre la transaction non terminée et
  la finalisation reprend de façon idempotente.
- **Catalogue** : un achat avec catalogue non chargé ou produit inconnu n'est
  jamais traité comme un abonnement ; il n'est pas complété et reste
  représentable par StoreKit.
- **Devises** : `/api/apple/products/` expose `business_price`,
  `business_currency`, `apple_price`, `apple_currency` (les anciens champs
  `price`/`currency` restent pour compatibilité). Le résumé reste à
  300 CDF et le produit Apple à 0,99 USD ; aucune conversion automatique.
- Aucun fichier Android ni FlexPay modifié. Aucune nouvelle migration pour
  ces corrections ; `payments 0009` reste la dernière.

## 12 ter. Limites connues de la réconciliation

La réconciliation locale s'appuie sur l'état écrit après `completePurchase`.
Deux fenêtres restent impossibles à prouver sans StoreKit :

1. **Arrêt entre le retour de `completePurchase` et l'écriture de l'état
   `completed`** : la réservation reste `backend_confirmed`. Le droit Django
   est acquis, mais l'application ne peut pas prouver localement que StoreKit
   a terminé. La réservation est conservée (jamais supprimée à l'aveugle).
2. **Arrêt pendant l'appel `completePurchase`** : même situation. Si StoreKit
   n'a pas terminé, il redélivre la transaction au lancement suivant et la
   finalisation reprend ; s'il a terminé, la transaction n'est pas redélivrée.

**Solution sûre pour ces deux cas** (hors périmètre de cette tâche, car elle
touche le backend ou l'interface) : exposer un état « finalisation en attente »
permanent dans le compte et un bouton « Reprendre la finalisation » qui appelle
`restorePurchases` pour forcer StoreKit à redélivrer les transactions non
terminées. Pour les résumés consommables, `restorePurchases` ne les restaure
pas ; il faudrait alors un mécanisme serveur de clôture manuelle validé par un
administrateur, jamais une purge temporelle côté client. Aucune de ces options
n'est implémentée ici.

**Autres limites** :
- une annulation reçue sans `purchaseID` ne libère pas la réservation
  (protection contre un événement ancien) ; le même résumé peut être réessayé,
  mais un autre résumé du même palier de prix reste bloqué jusqu'à résolution ;
- la détection de transaction « antérieure » dépend de
  `PurchaseDetails.transactionDate` ; si StoreKit ne le fournit pas, la
  première transaction est liée à la réservation (comportement voulu pour un
  premier achat), avec un risque résiduel documenté ;
- la vérification réelle de `completePurchase`, la redélivrance des
  transactions et les notifications Apple exigent un appareil iOS et un compte
  Sandbox.

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
