# Tâche 70 — « Payer pour un autre étudiant »

## Résumé

Un étudiant connecté peut payer un **résumé** ou un **abonnement QCM** pour un
autre étudiant. Le compte connecté reste le **payeur** ; le droit d'accès et la
notification vont exclusivement au **bénéficiaire**. Le parcours « Payer pour
moi » est inchangé.

La fonctionnalité est exposée uniquement sur **Android** (`!kIsWeb &&
defaultTargetPlatform == TargetPlatform.android`). Sur iOS et Web, le sélecteur
n'apparaît pas et le paiement reste identique à avant.

## Flux backend

1. L'application envoie `phone_number` (numéro Mobile Money du payeur) et,
   optionnellement, `beneficiary_phone`.
2. Le backend normalise le numéro payeur (`0XXXXXXXXX`) et **résout le
   bénéficiaire en base** :
   - `UserProfile.phone = numéro normalisé` ;
   - `user.is_active = True` ;
   - `profile.groupe = 'ETUDIANT'` ;
   - refus si plusieurs comptes partagent le numéro (409), si le compte est
     inactif/inexistant/non étudiant (404), ou si c'est le numéro du payeur.
3. La transaction `Purchase` est créée avec :
   - `user` = **bénéficiaire** (propriétaire du droit) ;
   - `payer` = compte connecté ;
   - `payer_phone` = numéro réellement utilisé ;
   - `beneficiary_phone` = numéro du bénéficiaire ;
   - `summary`/`service`, `amount`, `transaction_id`, `status`.
4. Après confirmation FlexPay, le callback :
   - verrouille la ligne (`select_for_update`) et ne traite que `pending` ;
   - marque `completed` une seule fois ;
   - crée l'`Abonnement` au nom du bénéficiaire, avec `payer` conservé ;
   - répond « déjà confirmé » à un callback répété (idempotence).
5. Les signaux de notifications utilisent `purchase.user` / `abonnement.user`
   (bénéficiaire). Le message devient « 🎁 Résumé offert » ou
   « 🎁 Abonnement offert ». Aucune notification d'attribution au payeur.

## Sécurité et intégrité

- Toutes les entrées sont validées côté serveur ; le numéro du bénéficiaire
  n'identifie jamais un compte directement, il sert à interroger la base.
- Refus des comptes inactifs, non étudiants, inexistants, ambigus et de son
  propre numéro.
- Refus d'un cadeau si le bénéficiaire possède déjà le résumé, un abonnement
  actif, ou un paiement cadeau en cours (anti-double débit).
- `transaction.atomic` + `select_for_update` sur le callback et la création
  d'abonnement ; deux callbacks simultanés ne créditent qu'une fois.
- Le payeur peut suivre la transaction (`check-status`) mais ne peut pas créer
  l'abonnement à sa place (`create-subscription-after-payment` reste filtré sur
  `user=request.user`).
- Aucun numéro complet n'est exposé dans les réponses API ni dans les logs
  Flutter. L'endpoint de vérification renvoie nom, numéro masqué et promotion,
  sans identifiant de compte.
- Les montants et références viennent du backend / du fournisseur, jamais de
  l'application.
- Le jeton API FlexPay n'est plus codé en dur : il est lu depuis
  `FLEXPAY_API_TOKEN` (environnement / `backend/.env`, ignoré par Git). Sans
  cette variable, l'initiation de paiement renvoie une erreur de configuration
  explicite au lieu d'utiliser un secret versionné.

## Interface Flutter

Widget réutilisable `PaymentRecipientSelector` :
- choix **Payer pour moi / Payer pour un autre** ;
- en mode cadeau : numéro du payeur prérempli (modifiable) + numéro du
  bénéficiaire + bouton **Vérifier** ;
- affichage de l'identité vérifiée (nom, numéro masqué, promotion) avant
  confirmation.

Intégré dans :
- achat d'un résumé depuis les détails du résumé (`summary_details_screen`) ;
- achat d'un résumé depuis l'écran de paiement (`purchase_summary_screen`) ;
- abonnement depuis la carte de service (`service_card`) ;
- abonnement QCM (`exercise_subscription_screen`).

`PaymentStatusScreen` distingue le cadeau : texte de succès adapté, badge
« Mes Achats » non incrémenté pour le payeur, pas de création d'abonnement côté
payeur.

## Tests exécutés

Commande :

```bash
cd backend
PYTHONIOENCODING=utf-8 python manage.py test payments.tests \
  --settings=resume_backend.settings_test
```

Résultat : **14 tests OK** (`Ran 14 tests ... OK`).

Couverts :
- vérification du bénéficiaire (succès, numéro personnel, inactif,
  non-étudiant, inconnu, format invalide) ;
- achat de résumé offert → attribué au bénéficiaire, payeur sans achat ;
- achat pour soi inchangé ;
- refus si le bénéficiaire possède déjà le résumé ;
- abonnement offert → `Purchase` et `Abonnement` au bénéficiaire, `payer` conservé ;
- refus si abonnement actif ou paiement cadeau déjà en cours ;
- suivi de la transaction par le payeur, refus pour un tiers ;
- callback réussi idempotent (un seul abonnement) ;
- callback échoué sans attribution ;
- notifications « offert » au bénéficiaire uniquement.

Compilation :
- `flutter analyze` sur les fichiers modifiés : aucune erreur ;
- `flutter build web --release --base-href=/` : OK (compilation Dart complète) ;
- `flutter build apk --debug` : OK (`app-debug.apk` produit localement, **non
  publié**).

## Non testé ici (nécessite un appareil / le fournisseur)

- Parcours tactile réel sur Android (sélecteur, vérification, paiement).
- Paiement FlexPay réel ou sandbox avec un numéro Mobile Money.
- Réception d'un push sur le bénéficiaire après un cadeau.
- Comportement sur iOS/Web : le sélecteur doit rester invisible (vérifié par
  le code, non exécuté sur appareil).

## Fichiers à déployer

Backend :

```
backend/payments/models.py
backend/payments/beneficiary.py
backend/payments/flexpay_integration.py
backend/payments/views.py
backend/payments/urls.py
backend/payments/tests.py
backend/payments/migrations/0007_abonnement_payer_purchase_beneficiary_phone_and_more.py
backend/notifications/tasks.py
```

Puis :

```bash
python manage.py migrate
```

Flutter (nouvelle build Android, **ne pas publier** dans le cadre de la tâche) :

```
lib/models/user.dart
lib/services/api_service.dart
lib/features/purchases/widgets/payment_recipient_selector.dart
lib/features/purchases/screens/payment_status_screen.dart
lib/features/purchases/screens/purchase_summary_screen.dart
lib/features/summary_details/screens/summary_details_screen.dart
lib/features/subscriptions/widgets/service_card.dart
lib/features/exercises/screens/exercise_subscription_screen.dart
```

Aucun fichier `android/` n'a été modifié.

## Point d'attention

L'endpoint `POST /api/beneficiary/verify/` est authentifié mais sans limitation
de débit dédiée (aucun throttling global n'est configuré dans le projet). Il
renvoie le nom du compte correspondant à un numéro. Si l'énumération de numéros
devient un risque, ajouter un throttle par utilisateur (ex. 20/min).
