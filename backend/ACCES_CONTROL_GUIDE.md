# Guide du Contrôle d'Accès Strict - Résumé+

## Vue d'ensemble

Le système implémente un contrôle d'accès strict basé sur trois niveaux hiérarchiques :
**Université → Promotion → Filière/Option**

## Règles de Sécurité

### 1. Principe de Base
- Un utilisateur (CP ou étudiant) ne peut accéder qu'aux données de **son université, sa promotion et sa filière**
- Aucun accès croisé entre universités, promotions ou filières n'est autorisé
- Les administrateurs ont accès à toutes les données

### 2. Modèles Concernés

#### Course (Cours)
- **Champs FK** : `universite_fk`, `filiere_fk`, `promotion_fk`
- **Anciens champs** : `university`, `filiere` (conservés pour compatibilité)
- **Filtrage** : Automatique selon le profil utilisateur

#### Session (Séances Audio)
- **Filtrage** : Via le cours associé (`course__universite_fk`, etc.)
- **Création** : Uniquement pour les cours accessibles

#### Summary (Résumés)
- **Filtrage** : Via le cours associé
- **Création** : CP et Admin uniquement
- **Accès** : Selon université/promotion/filière

## Permissions Django

### HasUniversityAccess
Vérifie que l'utilisateur a bien une université, promotion et filière définie.

```python
# Appliquée sur : CourseListCreateView, SessionListCreateView, SummaryListCreateView
permission_classes = [permissions.IsAuthenticated, HasUniversityAccess]
```

### CanModifyObject
Permet la modification uniquement au créateur ou à l'admin.

```python
# Appliquée sur : CourseDetailView, SessionDetailView
permission_classes = [permissions.IsAuthenticated, HasUniversityAccess, CanModifyObject]
```

## Filtrage Backend

### Exemple : CourseListCreateView
```python
def get_queryset(self):
    profile = self.request.user.profile
    
    if profile.is_admin:
        return Course.objects.all()
    
    return Course.objects.filter(
        universite_fk=profile.universite,
        promotion_fk=profile.promotion,
        filiere_fk=profile.filiere
    )
```

### Création Automatique
Lors de la création d'un cours, les champs FK sont automatiquement assignés :

```python
def perform_create(self, serializer):
    profile = self.request.user.profile
    serializer.save(
        universite_fk=profile.universite,
        promotion_fk=profile.promotion,
        filiere_fk=profile.filiere,
        university=profile.universite.nom,
        filiere=profile.filiere.nom
    )
```

## Migration des Données Existantes

### Script de Migration
Pour migrer les anciens cours vers le nouveau système :

```python
# backend/scripts/migrate_courses.py
from courses.models import Course, Universite, Filiere, Promotion

def migrate_courses():
    for course in Course.objects.all():
        # Trouver l'université correspondante
        if course.university:
            try:
                univ = Universite.objects.get(nom=course.university)
                course.universite_fk = univ
            except Universite.DoesNotExist:
                print(f"Université non trouvée: {course.university}")
        
        # Trouver la filière correspondante
        if course.filiere:
            try:
                fil = Filiere.objects.get(nom=course.filiere)
                course.filiere_fk = fil
            except Filiere.DoesNotExist:
                print(f"Filière non trouvée: {course.filiere}")
        
        # Assigner une promotion par défaut (à adapter)
        # course.promotion_fk = Promotion.objects.first()
        
        course.save()
```

### Exécution
```bash
python manage.py shell < backend/scripts/migrate_courses.py
```

## Tests de Sécurité

### Test 1 : Accès Croisé entre Universités
```python
# Créer 2 utilisateurs de 2 universités différentes
user1 = User.objects.create(username='user1')
user1.profile.universite = Universite.objects.get(nom='Université A')
user1.profile.save()

user2 = User.objects.create(username='user2')
user2.profile.universite = Universite.objects.get(nom='Université B')
user2.profile.save()

# User1 ne doit pas voir les cours de User2
# Tester via API : GET /api/courses/
```

### Test 2 : Modification d'URL
```bash
# Tenter d'accéder à un cours d'une autre université
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/courses/999/
# Doit retourner 404 si le cours n'appartient pas à l'université de l'utilisateur
```

### Test 3 : Création de Cours
```bash
# Un CP ne peut créer que des cours pour son université/promotion/filière
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"nom": "Nouveau Cours", "description": "Test"}' \
  http://localhost:8000/api/courses/
# Les champs FK doivent être automatiquement assignés
```

## Configuration Utilisateur

### Profil Utilisateur Requis
Chaque utilisateur doit avoir :
```python
user.profile.universite = Universite.objects.get(...)
user.profile.promotion = Promotion.objects.get(...)
user.profile.filiere = Filiere.objects.get(...)
user.profile.groupe = 'CP' ou 'ETUDIANT' ou 'ADMIN'
```

### Vérification
```python
# Dans Django shell
from django.contrib.auth.models import User

user = User.objects.get(username='test_user')
print(f"Université: {user.profile.universite}")
print(f"Promotion: {user.profile.promotion}")
print(f"Filière: {user.profile.filiere}")
print(f"Groupe: {user.profile.groupe}")
```

## Endpoints API Sécurisés

| Endpoint | Méthode | Filtrage | Permission |
|----------|---------|----------|------------|
| `/api/courses/` | GET | Par université/promotion/filière | HasUniversityAccess |
| `/api/courses/` | POST | Auto-assignation FK | HasUniversityAccess |
| `/api/courses/<id>/` | GET/PUT/DELETE | Par université/promotion/filière | HasUniversityAccess + CanModifyObject |
| `/api/sessions/` | GET | Via course FK | HasUniversityAccess |
| `/api/summaries/` | GET | Via course FK | HasUniversityAccess |
| `/api/summaries/` | POST | CP/Admin uniquement | CanCreateSummary |

## Logs et Monitoring

### Activer les logs de sécurité
```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'security.log',
        },
    },
    'loggers': {
        'courses.permissions': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

## Prochaines Étapes

1. ✅ Modèle Course mis à jour avec champs FK
2. ✅ Permissions créées (HasUniversityAccess, CanModifyObject)
3. ✅ Filtrage backend implémenté
4. ✅ Migrations appliquées
5. ⏳ Migrer les données existantes
6. ⏳ Mettre à jour le frontend Flutter
7. ⏳ Tests de sécurité complets

## Support

Pour toute question sur le système de contrôle d'accès, consulter :
- `backend/courses/permissions.py` - Définitions des permissions
- `backend/courses/views.py` - Implémentation du filtrage
- `backend/courses/models.py` - Modèles avec méthode `is_accessible_by_user()`
