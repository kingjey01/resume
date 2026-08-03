"""
Script de migration pour convertir les anciens cours (CharField) vers les nouveaux (ForeignKey)
Exécution: python manage.py shell < scripts/migrate_courses_to_fk.py
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from courses.models import Course, Universite, Filiere, Promotion

def migrate_courses():
    """Migrer les anciens cours vers le nouveau système FK"""
    
    print("=" * 60)
    print("MIGRATION DES COURS VERS LE SYSTÈME FK")
    print("=" * 60)
    
    total_courses = Course.objects.count()
    migrated = 0
    errors = 0
    
    print(f"\nTotal de cours à migrer: {total_courses}")
    print("\nDébut de la migration...\n")
    
    for course in Course.objects.all():
        try:
            # Vérifier si déjà migré
            if course.universite_fk and course.filiere_fk and course.promotion_fk:
                print(f"✓ Cours '{course.nom}' déjà migré")
                migrated += 1
                continue
            
            # Migrer l'université
            if course.university and not course.universite_fk:
                try:
                    univ = Universite.objects.get(nom__iexact=course.university.strip())
                    course.universite_fk = univ
                    print(f"  → Université: {course.university} → {univ.nom}")
                except Universite.DoesNotExist:
                    # Créer l'université si elle n'existe pas
                    univ = Universite.objects.create(nom=course.university.strip())
                    course.universite_fk = univ
                    print(f"  → Université créée: {univ.nom}")
                except Universite.MultipleObjectsReturned:
                    univ = Universite.objects.filter(nom__iexact=course.university.strip()).first()
                    course.universite_fk = univ
                    print(f"  → Université (multiple): {univ.nom}")
            
            # Migrer la filière
            if course.filiere and not course.filiere_fk:
                try:
                    fil = Filiere.objects.get(nom__iexact=course.filiere.strip())
                    course.filiere_fk = fil
                    print(f"  → Filière: {course.filiere} → {fil.nom}")
                except Filiere.DoesNotExist:
                    # Créer la filière si elle n'existe pas
                    fil = Filiere.objects.create(nom=course.filiere.strip())
                    course.filiere_fk = fil
                    print(f"  → Filière créée: {fil.nom}")
                except Filiere.MultipleObjectsReturned:
                    fil = Filiere.objects.filter(nom__iexact=course.filiere.strip()).first()
                    course.filiere_fk = fil
                    print(f"  → Filière (multiple): {fil.nom}")
            
            # Assigner une promotion par défaut si non définie
            if not course.promotion_fk:
                # Essayer de trouver une promotion appropriée
                # Par défaut, utiliser L1 ou créer une promotion générique
                try:
                    promo = Promotion.objects.get(nom='L1')
                except Promotion.DoesNotExist:
                    promo = Promotion.objects.create(nom='L1', annee=2024)
                    print(f"  → Promotion créée: {promo.nom}")
                
                course.promotion_fk = promo
                print(f"  → Promotion assignée: {promo.nom}")
            
            # Sauvegarder
            course.save()
            migrated += 1
            print(f"✓ Cours '{course.nom}' migré avec succès\n")
            
        except Exception as e:
            errors += 1
            print(f"✗ Erreur pour le cours '{course.nom}': {str(e)}\n")
    
    print("=" * 60)
    print("RÉSUMÉ DE LA MIGRATION")
    print("=" * 60)
    print(f"Total de cours: {total_courses}")
    print(f"Migrés avec succès: {migrated}")
    print(f"Erreurs: {errors}")
    print("=" * 60)
    
    # Vérification finale
    print("\nVÉRIFICATION FINALE:")
    courses_without_fk = Course.objects.filter(
        universite_fk__isnull=True
    ) | Course.objects.filter(
        filiere_fk__isnull=True
    ) | Course.objects.filter(
        promotion_fk__isnull=True
    )
    
    if courses_without_fk.exists():
        print(f"⚠ {courses_without_fk.count()} cours n'ont pas tous les champs FK remplis:")
        for c in courses_without_fk[:5]:
            print(f"  - {c.nom} (ID: {c.id})")
    else:
        print("✓ Tous les cours ont été migrés avec succès!")

if __name__ == '__main__':
    migrate_courses()
