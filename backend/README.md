# Backend Django - Résumé+

## Installation et Configuration

### 1. Créer un environnement virtuel
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configuration de la base de données
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Créer un superutilisateur
```bash
python manage.py createsuperuser
```

### 5. Charger les données fictives
```bash
python manage.py seeddata
```

### 6. Lancer le serveur
```bash
python manage.py runserver
```

## API Endpoints

### Authentification
- `POST /api/auth/register/` - Inscription
- `POST /api/auth/login/` - Connexion
- `POST /api/auth/token/refresh/` - Rafraîchir le token
- `GET /api/auth/profile/` - Profil utilisateur
- `PUT /api/auth/profile/update/` - Mettre à jour le profil

### Cours
- `GET /api/courses/courses/` - Liste des cours
- `POST /api/courses/courses/` - Créer un cours
- `GET /api/courses/courses/{id}/` - Détail d'un cours

### Sessions
- `GET /api/courses/sessions/` - Liste des sessions
- `POST /api/courses/sessions/` - Créer une session

### Résumés
- `GET /api/courses/summaries/` - Liste des résumés
- `POST /api/courses/summaries/` - Créer un résumé
- `POST /api/courses/generate-summary/` - Générer résumé IA

### Paiements
- `GET /api/payments/purchases/` - Historique des achats
- `POST /api/payments/purchases/` - Créer un achat
- `POST /api/payments/purchases/{id}/complete/` - Finaliser un achat

### Sécurité
- `GET /api/security/logs/` - Logs de sécurité
- `POST /api/security/log-event/` - Enregistrer un événement

## Documentation API
- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/redoc/`

## Utilisateurs de test
- CP: `cp_alice` / `password123`
- Étudiant: `student1` / `password123`
