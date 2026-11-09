# Tâche 72 — Déploiement backend et préparation iOS

Date : 2026-11-09
Serveur : `vps` (180.149.197.29:1303), site
`/home/jey/resumecours.gestionhospitaliare.site/backend`.
Serveur web : Apache + mod_wsgi (daemon `resumecours`, 4 processus),
venv `env39` (Python 3.9.18), PostgreSQL `resumecours_db_new` (13 Mo).

## 1. Sauvegardes effectuées avant déploiement

Dossier local : `resume/backup_deploy_20261109/`

| Fichier | Rôle |
|---|---|
| `apple_iap.py.server` | version serveur avant déploiement |
| `apple_views.py.server` | version serveur avant déploiement |
| `seed_deployment.py.server` | version serveur avant déploiement |
| `requirements.txt.server` | état serveur (non déployé) |
| `db_resumecours_20261109.sql.gz` | dump complet PostgreSQL (`pg_dump`, 53 tables) |
| `SHA256SUMS.txt` | empreintes de tous les fichiers ci-dessus |

Le dump a été produit sur le serveur en streaming vers le poste : aucun
fichier de sauvegarde n'a été écrit sur le serveur.

## 2. Contrôle des migrations

```
payments 0001 → 0009 : toutes appliquées
users    0001 → 0013 : toutes appliquées
showmigrations --plan : aucune migration en attente
```

Aucune migration n'a donc été exécutée. Aucune écriture en base.

## 3. Fichiers déployés

Uniquement trois fichiers, aux chemins exacts du backend :

| Fichier | SHA-256 local = serveur |
|---|---|
| `payments/apple_iap.py` | `c61fdfbc…82dd00` |
| `payments/apple_views.py` | `3f0e2256…24d62` |
| `payments/management/commands/seed_deployment.py` | `c3530d32…c3e04` |

Non déployés volontairement : `requirements.txt` (le fichier serveur est un
ancien inventaire qui ne correspond pas à l'environnement installé ; les
paquets nécessaires sont déjà présents, dont `app-store-server-library`),
`tests_apple.py` (hors runtime), `.env` (déjà configuré),
`resume_backend/settings*.py` (le serveur utilise le paquet `backend`, et
`APPLE_ALLOWED_ENVIRONMENTS` y est déjà présent).

Aucune modification de `android/`, de FlexPay, des prix, des identifiants
produits Apple, ni des autres vhosts. Aucun redémarrage d'Apache : rechargement
mod_wsgi par mise à jour de `backend/wsgi.py`, qui réimporte l'application.

## 4. Vérifications exécutées

```
python manage.py check
  → System check identified no issues (0 silenced)

GET  /api/health/                    → 200
GET  /api/apple/products/            → 200
POST /api/apple/verify/              → 401 (authentification requise)
POST /api/apple/notifications/       → 400 (signature Apple invalide refusée)
```

Le catalogue renvoie bien les nouveaux champs :

- `summary.300` : `business_price=300`, `business_currency=CDF`,
  `apple_price=0.99`, `apple_currency=USD` ;
- abonnement QCM : `business_price=500.00`, `business_currency=CDF`.

Le journal Apache montre le réimport WSGI à 21:44 et aucune erreur Python.

Tests backend locaux sur les mêmes fichiers :

```
manage.py test payments.tests_apple --settings=resume_backend.settings_test
  → 23 tests OK
```

Configuration Apple constatée sur le serveur (noms uniquement, sans valeurs) :

| Variable | État |
|---|---|
| `APPLE_BUNDLE_ID` | renseigné |
| `APPLE_ENVIRONMENT` | `Sandbox` |
| `APPLE_ALLOWED_ENVIRONMENTS` | `Sandbox` |
| `APPLE_SUMMARY_PRODUCTS` | renseigné (summary.300) |
| `APPLE_ISSUER_ID` | vide |
| `APPLE_KEY_ID` | vide |
| `APPLE_PRIVATE_KEY_PATH` | vide |
| `APPLE_APP_APPLE_ID` | vide |

Les certificats racines Apple G2/G3 sont présents. `/verify` et
`/notifications` n'utilisent que `SignedDataVerifier` (certificats + bundle) :
les quatre variables vides ne bloquent pas ces endpoints. Elles ne deviennent
nécessaires que pour un appel à l'App Store Server API.

## 5. Version Flutter iOS préparée

- `pubspec.yaml` : `1.1.22+70` → **`1.1.23+71`** (le contrôle Codemagic exige
  un build number > 68).
- `flutter test test/apple_iap_pending_summary_test.dart` → **19 tests OK**.
- `flutter analyze` sur le service IAP, les types, la réservation en attente,
  le bouton Apple et le test → **No issues found**.
- Le build IPA ne peut pas être produit sur ce poste Windows. Le workflow
  Codemagic `ios-release` (`codemagic.yaml`, branche
  `feat/tache60-catalogue-perf`) est prêt. Il lit le numéro de build dans
  `pubspec.yaml`, reconstruit les Pods et publie l'IPA.
- `submit_to_testflight: false` : le binaire est monté pour les testeurs
  internes, sans revue bêta.

**Action requise avant build** : les corrections de la tâche 72 sont encore
non commitées. Codemagic construit un commit : il faut committer et pousser sur
`feat/tache60-catalogue-perf` avant de lancer le workflow.

## 6. Test Sandbox — non exécuté ici

Aucun appareil iOS ni compte Sandbox n'est disponible dans cet environnement.
Les scénarios suivants ne sont donc **pas déclarés validés** :

1. achat réel d'un résumé consommable ;
2. annulation depuis la feuille Apple ;
3. validation backend de la transaction signée ;
4. reprise d'une transaction interrompue.

Procédure prête à exécuter sur iPhone :

1. committer/pousser, lancer Codemagic `ios-release`, installer la build via
   TestFlight (testeur interne) ;
2. sur l'iPhone : Réglages → App Store → compte Sandbox ;
3. achats à tester avec `APPLE_ENVIRONMENT=Sandbox` côté serveur ;
4. contrôles attendus :
   - achat : `/api/apple/verify/` 200, `Purchase.source='apple'`,
     `AppleTransaction` créée, UI « Achat Apple confirmé » ;
   - annulation : aucun `Purchase`, message « Achat annulé » ;
   - rejouer la même transaction : réponse idempotente, pas de second droit ;
   - tuer l'app après validation backend mais avant `completePurchase` :
     au relancement, StoreKit redélivre la transaction, le droit n'est pas
     redonné une seconde fois, l'état revient à `completed`.
5. notifications : l'URL doit être configurée dans App Store Connect
   (`https://resumecours.gestionhospitaliare.site/api/apple/notifications/`),
   puis vérifier `AppleNotification` après un achat Sandbox.

## 7. Retour arrière

1. recopier `backup_deploy_20261109/*.server` aux chemins serveur ;
2. mettre à jour `backend/wsgi.py` pour recharger mod_wsgi ;
3. `python manage.py check` ;
4. en cas de besoin, restaurer le dump :
   `gunzip -c db_resumecours_20261109.sql.gz | psql …` (à valider avant usage).

Aucune migration à annuler.
