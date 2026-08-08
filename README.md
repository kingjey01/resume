# 📚 Résumé+ — Application Mobile de Résumés Intelligents

**Résumé+** est une application mobile éducative qui transforme les cours en résumés clairs et concis grâce à l'intelligence artificielle. Elle permet aux étudiants d'enregistrer leurs séances audio, de générer des résumés intelligents, d'acheter des résumés et de s'exercer avec des QCM personnalisés.

---

## ✨ Fonctionnalités Principales

### 🎙️ Audio → Texte → Résumé IA
- Enregistrement audio (micro) ou importation de fichiers (MP3, WAV, OGG, M4A)
- Transcription automatique via **Deepgram**
- Génération de résumés intelligents via **DeepSeek** (LLM)
- Résumés structurés en Markdown (titres `##`, gras, listes, tableaux, citations)
- Blocs de code avec langage indiqué (```python, ```javascript, etc.)
- Formules mathématiques en LaTeX (`$$...$$`)

### 🛒 Marketplace de Résumés
- Résumés gratuits et payants
- Achat via **FlexPay** (Mobile Money)
- Déverrouillage **instantané** après paiement (toutes les vues se rafraîchissent)
- Protection du contenu : téléchargement désactivé, anti-capture d'écran
- Aperçu limité (150 caractères) pour les résumés non achetés

### 📝 QCM & Exercices Personnalisés (Anti-triche)
- **1 exercice unique par utilisateur et par résumé** (`UserPersonalizedExercise`)
- Questions générées avec un **seed aléatoire** injecté dans le prompt IA
- Difficultés : Facile / Moyen / Difficile (8 questions chacune)
- Blocs techniques (`code_block` / `code_language`) affichés dans les questions et corrections
- Historique des tentatives individuel (`UserPersonalizedAttempt`)
- Abonnement requis pour générer des QCM

### 🔊 Lecture Audio (TTS)
- Synthèse vocale via `flutter_tts` (Android/iOS/Web)
- Lecture complète des résumés longs (découpage intelligent en chunks)
- Contrôles : play, pause, reprise, arrêt, vitesse
- Vitesse constante après pause/reprise

### 🔐 Authentification (Téléphone + OTP)
- Connexion **uniquement** par numéro de téléphone + code OTP reçu par SMS
- Le système username/password a été **entièrement supprimé** de l'application (écrans, routes, méthodes API)
- Profil complété à la première connexion (nom, université, promotion, filière)
- **Suppression de compte** : confirmation par code OTP SMS, puis redirection automatique vers la connexion par téléphone
- **Contenu préservé à la suppression** : les résumés, sessions et exercices publiés par un CP supprimé restent accessibles (auteur anonymisé → « Inconnu ») — les achats des étudiants qui ont payé ce contenu ne sont **jamais perdus**

### 🔔 Notifications
- Notifications push **Firebase Cloud Messaging (FCM)**
- Ciblage individuel (jamais de broadcast pour paiements/abonnements)
- Badge sur l'icône de l'application (Android via ShortcutBadger, iOS natif)
- Centre de notifications : recherche, filtres, pagination infinie, "Tout lire"
- **Emails de statut CP** (approbation/refus) envoyés en **arrière-plan via Celery** (`users/tasks.py`) avec relance automatique — le commentaire de l'admin est inclus dans l'email de refus
- **Notification admin** : à chaque nouvelle demande CP, l'administration reçoit un email (jamais de push) — destinataires dynamiques via `ADMIN_NOTIFICATION_EMAIL` dans `.env` (plusieurs emails séparés par des virgules)

### 👥 Rôles
| Rôle | Rôle |
|------|------|
| **CP (Chef de Promotion)** | Dépose une demande avec **email de contact** (notifié par email + push à l'approbation/refus), crée professeurs, cours, associations (Dispense), enregistre les séances, valide les résumés |
| **Étudiant** | Consulte, achète et écoute les résumés, passe les QCM |

### 💾 Brouillons Audio Locaux
- Sauvegarde automatique après chaque enregistrement
- Jusqu'à **5 brouillons** simultanés
- Restauration automatique à la réouverture de l'écran
- Suppression après envoi réussi ou action volontaire

### ⚙️ Systèmes de Configuration Dynamique
- **Force Update** : version minimale obligatoire, mode maintenance, message personnalisé (table `AppVersion`)
- **Prix minimum dynamique** : seuil des résumés configurable en admin (table `ResumePricingConfig`)
- **Mode test Google Play** : OTP fixe "1234" + code renvoyé dans l'API pour auto-soumission (numéros de test uniquement)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FLUTTER (Frontend)               │
│  Riverpod · Dio · flutter_tts · record · FCM        │
│  flutter_local_notifications · flutter_markdown     │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS / REST
┌──────────────────────▼──────────────────────────────┐
│                    DJANGO (Backend)                 │
│  DRF · SimpleJWT · Celery · Redis · FCM Admin       │
│  ┌─────────┐ ┌──────────┐ ┌──────────────┐          │
│  │ courses │ │ payments │ │ notifications │        │
│  │ users   │ │ security │ └──────────────┘          │
│  └─────────┘ └──────────┘                           │
└───────┬──────────────────────────────┬──────────────┘
        │                              │
   ┌────▼────┐                   ┌─────▼─────┐
   │ Deepgram│                   │  DeepSeek │
   │(transc.)│                   │  (LLM IA) │
   └─────────┘                   └───────────┘
        │                              │
        └──────────┬───────────────────┘
                   ▼
        ┌─────────────────────┐
        │   FlexPay (Mobile   │
        │      Money)         │
        └─────────────────────┘
```

## 📁 Structure du Projet

```
resume_plus_clean/
├── lib/                      # Frontend Flutter
│   ├── features/             # Modules par fonctionnalité
│   │   ├── auth/             # Connexion, OTP, profil
│   │   ├── home/             # Accueil, cours, résumés
│   │   ├── exercises/        # QCM, résultats, abonnement
│   │   ├── notifications/    # Centre de notifications
│   │   ├── onboarding/       # Parcours d'introduction
│   │   ├── purchases/        # Achat, statut paiement
│   │   ├── settings/         # Paramètres, politique, conditions
│   │   ├── splash/           # Écran de démarrage + force update
│   │   ├── subscriptions/    # Abonnements, services
│   │   ├── summaries/        # Résumés achetés
│   │   ├── summary_details/  # Détail d'un résumé
│   │   ├── upload/           # Enregistrement, saisie manuelle
│   │   └── validation/       # Validation des résumés (CP)
│   ├── models/               # Modèles de données Flutter
│   ├── providers/            # Riverpod providers
│   ├── services/             # Services (API, TTS, FCM, badge...)
│   ├── widgets/              # Composants réutilisables
│   └── theme/                # Thème (clair/sombre, Poppins)
│
├── backend/                  # Backend Django
│   ├── courses/              # Cours, résumés, exercices, dispenses
│   ├── payments/             # Services, abonnements, FlexPay
│   ├── notifications/        # FCM, notifications push
│   ├── users/                # Auth OTP, profils, demandes CP, emails Celery
│   ├── security/             # Logs, AppVersion, ResumePricingConfig
│   └── resume_backend/       # Configuration Django (settings, urls)
│
├── android/                  # Configuration Android
├── ios/                      # Configuration iOS
└── website/                  # Site statique (politique, conditions, guide)
```

## 🔧 Services Clés

### Backend
| Service | Fichier | Rôle |
|---------|---------|------|
| DeepSeek | `backend/courses/deepseek_service.py` | Résumés, QCM, traduction, reformulation, simplification |
| Deepgram | `backend/courses/deepgram_service.py` | Transcription audio |
| AudioProcessor | `backend/courses/audio_processing.py` | Pipeline audio → transcription → résumé |
| Exercices personnalisés | `backend/courses/personalized_exercise_generator.py` | QCM uniques par utilisateur |
| FlexPay | `backend/payments/flexpay_integration.py` | Paiement Mobile Money |
| Notifications | `backend/notifications/tasks.py` | FCM + notifications en base |
| Emails CP | `backend/users/tasks.py` | Emails approbation/refus CP + notification admin nouvelle demande (Celery, relance auto) |
| Signaux | `backend/payments/signals.py` | Déclenchement automatique des notifications |

### Frontend
| Service | Fichier | Rôle |
|---------|---------|------|
| API | `lib/services/api_service.dart` | Client HTTP, refresh token, gestion d'erreurs centralisée |
| Audio | `lib/services/audio_service.dart` | TTS robuste (chunks, pause/reprise) |
| Enregistrement | `lib/services/mobile_audio_recorder.dart` | Recorder universel (mobile + web) |
| Brouillons | `lib/services/audio_draft_service.dart` | Brouillons audio locaux (5 max) |
| Badge | `lib/services/badge_service.dart` | Badge sur icône (MethodChannel) |
| Notifications | `lib/services/notification_service.dart` | Polling compteur non-lus |
| FCM | `lib/services/fcm_service.dart` | Firebase Cloud Messaging |
| Version | `lib/services/version_service.dart` | Force update / maintenance |

## 🎨 Widgets Réutilisables

| Widget | Rôle |
|--------|------|
| `AiContentView` | Rendu Markdown complet (titres, code, tableaux, citations, pagination) |
| `TechBlockWidget` | Blocs techniques (code, formule, algorithme) — même style que les résumés |
| `AudioPlayerWidget` | Lecture audio TTS |
| `ErrorHandlerMixin` | Gestion d'erreurs unifiée (messages utilisateur clairs) |
| `SecureScreenWrapper` | Protection anti-capture d'écran |

## 🚀 Démarrage

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configuration
cp .env.example .env  # Renseigner les clés (DB, DeepSeek, Deepgram, FlexPay, FCM)

# Migrations
python manage.py makemigrations
python manage.py migrate
python manage.py seed_production

# Celery (transcription, résumés asynchrones, notifications, emails CP)
celery -A resume_backend worker -l info --concurrency=2

# Serveur
python manage.py runserver
```

### Frontend
```bash
flutter pub get
flutter run
```

## 📊 Principaux Endpoints API

| Endpoint | Rôle |
|----------|------|
| `POST /api/auth/otp/request/` | Demande de code OTP |
| `POST /api/auth/otp/verify/` | Vérification OTP + connexion JWT |
| `POST /api/auth/cp-request/` | Création demande CP (motivation + email de contact) |
| `GET /api/auth/cp-request/status/` | Statut de la demande CP |
| `POST /api/auth/delete-account/request-otp/` | Envoi du code OTP de confirmation de suppression |
| `DELETE /api/auth/delete-account/` | Suppression du compte (après vérification OTP) |
| `GET /api/courses/` | Liste des cours |
| `GET /api/summaries/` | Liste des résumés |
| `POST /api/courses/sessions/upload-audio/` | Upload audio de session |
| `POST /api/summaries/<id>/generate-exercise/` | Génération d'exercice |
| `POST /api/exercises/<id>/submit/` | Soumission des réponses |
| `POST /api/purchases/initiate/` | Initiation achat résumé |
| `POST /api/initiate-subscription-payment/` | Initiation abonnement |
| `GET /api/app-version/` | Configuration force update |
| `GET /api/resume-pricing-config/` | Prix minimum dynamique |
| `GET /api/notifications/` | Liste des notifications |

## 🌐 Site Web

Le dossier `website/` contient un site statique responsive (politique de confidentialité, conditions d'utilisation, guide d'utilisation) prêt pour Google Play Console.

## 🛡️ Sécurité

- Authentification JWT (SimpleJWT) + OTP par SMS (téléphone uniquement — username/password retiré)
- Protection anti-capture d'écran (Android) activée globalement au démarrage
- Téléchargement des résumés désactivé
- Notifications individuelles (pas de broadcast)
- Exercices uniques par utilisateur (anti-triche)
- Messages d'erreur utilisateur (pas de DioException brute)

## 🧪 Mode Test Google Play

```python
# .env
OTP_TEST_MODE=True
OTP_TEST_PHONE_NUMBERS=["+243990000000", "+243990000001"]
```

Les numéros de test ne reçoivent pas de SMS : le code est renvoyé dans l'API et **soumis automatiquement** par l'application (le testeur ne tape rien).
