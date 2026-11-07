# Rapport de faisabilité — Muhtasari+ en PWA

Date : 2026-11-04
Périmètre : cible **Web / PWA uniquement**. Aucune modification Android, iOS,
signature, package ID ni paiement mobile.

## 1. Conclusion

**La version Web/PWA est faisable sans toucher à Android.**

`flutter build web --release` compile déjà le projet avec succès
(≈ 73 s, sortie `build/web`, `main.dart.js` ≈ 5,2 Mo). Le projet contient
déjà des gardes web (`kIsWeb`), des fichiers *stub* pour `dart:io` et une
implémentation web de l'audio. Il manque surtout la couche PWA (manifeste,
icônes, splash, service worker de cache).

## 2. Environnement constaté

| Élément | Valeur |
|---|---|
| Flutter | 3.47.7 stable (`C:\flutter`) |
| Projet | `resume_plus_clean` — version 1.1.21+68 |
| API | `https://resumecours.gestionhospitaliare.site/api` |
| Build web | ✅ réussi (`dart2js`, renderer CanvasKit) |
| CORS backend | déjà ouvert (`CORS_ALLOW_ALL_ORIGINS` en production) |
| Web existant | `web/` contient `index.html`, `manifest.json`, `sw.js`, icônes par défaut |

Remarque Wasm : le *dry run* Wasm signale `flutter_secure_storage_web` et
`flutter_tts` comme incompatibles Wasm. Le build JavaScript n'est pas affecté ;
la PWA sera livrée en JavaScript (pas en `--wasm`).

## 3. Compatibilité des dépendances

### Compatibles Web

- `dio`, `shared_preferences`, `cached_network_image`, `lottie`, `intl`,
  `shimmer`, `go_router`, `url_launcher`, `package_info_plus`,
  `image_picker`, `file_picker`, `audioplayers`, `flutter_tts`.
- `flutter_secure_storage` : implémentation Web via WebCrypto, **HTTPS requis**.
- `record` 5.x : `record_web` présent (MediaRecorder). L'application désactive
  toutefois l'enregistrement sur Web via `record_audio_screen_web_safe.dart`.

### Mobile uniquement (neutralisés sur Web)

| Package | Traitement |
|---|---|
| `firebase_core` / `firebase_messaging` | `Firebase.initializeApp()` dans un `try/catch` ; FCM et badge non initialisés si `kIsWeb` |
| `flutter_local_notifications` | utilisé uniquement dans `fcm_service`, non appelé sur Web |
| `flutter_foreground_task` | appels neutralisés par `kIsWeb`, sauf `initCommunicationPort()` à protéger |
| `background_downloader` | import conditionnel (`dart.library.io`), stub Web |
| `path_provider` / `dart:io` | usage dans des services non exécutés sur Web ; stubs présents |
| `screen_protector` | branche Web CSS (`screen_security_service`) |

## 4. Analyse fonctionnelle

| Fonction | Web / PWA |
|---|---|
| Connexion / OTP | ✅ REST + Dio ; jeton stocké en secure storage (HTTPS) |
| Cours et résumés | ✅ API existante |
| Achats existants | ✅ API existante |
| Paiements FlexPay | ✅ initiation + polling backend ; le paiement se valide sur le téléphone (USSD). Aucun SDK natif requis |
| Abonnements et QCM | ✅ API existante |
| Lecture audio | ✅ octets téléchargés par Dio + `audioplayers` Web |
| Enregistrement audio | ✅ activé côté Web via `record_web` (MediaRecorder) : Opus/WebM ou AAC/MP4 selon le navigateur, envoi des octets réels comme sur mobile |
| Téléchargement de documents | ✅ téléchargement d'octets via Dio ; le bouton « télécharger » des résumés gratuits affiche encore « bientôt disponible » |
| Notifications | ✅ liste et compteur non lus (polling) ; ✅ push Web intégré (FCM + `firebase-messaging-sw.js`) — il ne reste qu'à renseigner la config Firebase Web et la clé VAPID |
| Stockage local | ✅ `shared_preferences` (localStorage) + secure storage (WebCrypto, HTTPS) |

## 5. Écarts PWA constatés (avant travaux)

1. `manifest.json` générique : description Flutter par défaut, couleurs
   `#0175C2`, pas de `lang`, pas de `scope`, `start_url` ambigu.
2. `index.html` générique : description par défaut, pas de `viewport`, pas de
   `theme-color`, pas d'écran de lancement, icône Apple en 192 seulement.
3. `sw.js` **n'est pas enregistré** ; le service worker généré par Flutter
   s'auto-désinscrit (aucun cache, aucun fonctionnement hors ligne).
4. Icônes par défaut, non issues du logo de l'application.
5. `FlutterForegroundTask.initCommunicationPort()` est appelé sans garde Web.

## 6. Adaptations réalisées (Web uniquement)

- `web/flutter_bootstrap.js` personnalisé : n'appelle plus
  `serviceWorkerSettings`, ce qui désactive le service worker déprécié de
  Flutter et laisse la main à `sw.js`.
- `web/sw.js` : service worker PWA — pré-cache du shell (13 URL), network-first
  pour le code et la navigation, stale-while-revalidate pour les assets,
  nettoyage des anciens caches, repli SPA hors ligne.
- `web/index.html` : `viewport`, `theme-color`, métadonnées iOS/PWA, écran de
  lancement aux couleurs de la marque (masqué au premier rendu Flutter),
  enregistrement de `sw.js`.
- `web/manifest.json` : nom, description, `lang`, `scope`, `display`
  standalone, couleurs `#1A237E` / `#0D1642`, icônes.
- Icônes générées depuis `assets/LogoApp.png` : 192, 512, maskable 192/512,
  Apple 180, favicon 64.
- `web/firebase-config.js` : **généré** par
  `tool/generate_firebase_config.dart` depuis `.env.pwa` (ignoré par Git, jamais
  commité) ; `web/firebase-messaging-sw.js` : notifications push en
  arrière-plan et clic.
- `lib/services/fcm_service.dart` : branche Web ajoutée (Firebase Web,
  `getToken(vapidKey)`, enregistrement `device_type = 'web'`, rafraîchissement
  du badge au message). Le comportement mobile est inchangé.
- Enregistrement audio Web : `record_web` réellement utilisé,
  `web_blob_reader_*` récupère les octets du blob, `RecordAudioScreenWebSafe`
  enregistre et envoie via `ApiService.uploadAudio`.
- `lib/main.dart` : `initCommunicationPort()` protégé par `if (!kIsWeb)` ;
  initialisation Firebase Web confiée au service Web.
- Bundle final construit avec `--base-href=/` pour le domaine de production
  `https://resumecours.gestionhospitaliare.site/`.

## 7. Risques et limites

- **HTTPS obligatoire** (service worker, secure storage). Le domaine de
  production est déjà en HTTPS.
- **Push Web** : code intégré, mais il faut renseigner la configuration
  Firebase Web et la clé VAPID dans `.env.pwa` (console Firebase), puis lancer
  `dart run tool/generate_firebase_config.dart`. Aucune clé n'est commitée.
  Sans elles, le push est simplement désactivé ; la liste et le badge restent
  fonctionnels par polling.
- **Safari iOS** : installation via « Partager → Sur l'écran d'accueil » ;
  Web Push iOS 16.4+ fonctionne pour une PWA installée et autorisée. Les
  limites de stockage/cache Safari s'appliquent, le service worker reste
  fonctionnel en HTTPS.
- **Enregistrement audio Web** : nécessite le micro et HTTPS ; l'onglet doit
  rester ouvert (pas d'enregistrement en arrière-plan dans un navigateur).
- **Google Fonts** : `google_fonts` peut charger Poppins depuis le réseau ;
  les fichiers Poppins sont aussi embarqués dans l'app.
- **Mise à jour** : le service worker sert le code en network-first ; un
  rechargement récupère la nouvelle version.
- **Android** : aucun fichier `android/`, `ios/`, signature, package ID ou
  version modifié. Aucune build Android n'est produite par cette mission.

## 8. Tests réalisés en local

- `flutter build web --release --base-href=/` : ✅.
- PWA servie à la racine dans Chrome headless :
  - rendu Flutter : ✅ (`flutter-view` présent, splash retiré) ;
  - service worker : ✅ `activé`, cache `muhtasari-pwa-v1` rempli ;
  - `firebase-config.js` chargé : ✅ (`window.MUHTASARI_FIREBASE_CONFIG` et
    `MUHTASARI_VAPID_KEY` présents) ; push désactivé proprement tant que les
    valeurs `REMPLACER` sont en place ;
  - rechargement **hors connexion** : ✅ l'application démarre depuis le cache.
- `node --check web/sw.js` et `firebase-messaging-sw.js` : syntaxe valide.
- `flutter analyze` sur les fichiers modifiés : aucune erreur.
- Android : aucun fichier `android/` modifié, aucune build produite.

**Non testé ici** (nécessite un appareil, le déploiement et les clés Firebase) :
installation PWA sur Safari iPhone/iPad, installation Chrome Android,
connexion réelle, paiement FlexPay, enregistrement et lecture audio réels,
réception d'un push Web. À faire en Phase 5 après mise en ligne.

## 9. Livraison

- Build Web final : `build/web/` (base href `/app/`).
- Rapport : `RAPPORT_PWA_FAISABILITE.md`.
- Procédure de déploiement : `DEPLOIEMENT_PWA.md`.

Le déploiement (Phase 4) nécessite l'accès au serveur : les fichiers doivent
être copiés dans un répertoire servi en HTTPS, avec une règle SPA (repli vers
`index.html`) et sans écraser les fichiers Android.
