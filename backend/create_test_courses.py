#!/usr/bin/env python3
"""
Script pour créer des cours de test dans la base de données
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from courses.models import Course, Universite, Filiere, Promotion
from django.utils import timezone

def create_test_courses():
    print("🎓 CRÉATION DE COURS DE TEST")
    print("=" * 50)
    
    # 1. Vérifier les universités existantes
    print("\n1. Vérification des universités...")
    universites = Universite.objects.all()
    print(f"Universités trouvées: {universites.count()}")
    for univ in universites:
        print(f"  - {univ.nom}")
    
    # 2. Vérifier les filières existantes
    print("\n2. Vérification des filières...")
    filieres = Filiere.objects.all()
    print(f"Filières trouvées: {filieres.count()}")
    for filiere in filieres:
        print(f"  - {filiere.nom}")
    
    # 3. Créer des cours de test
    print("\n3. Création de cours de test...")
    
    # Utiliser la première université et filière disponibles
    if universites.exists() and filieres.exists():
        universite = universites.first()
        filiere = filieres.first()
        
        cours_test = [
            {
                'nom': 'Mathématiques Générales',
                'filiere': filiere.nom,
                'description': 'Cours de mathématiques de base couvrant l\'algèbre et l\'analyse',
                'university': universite.nom,
            },
            {
                'nom': 'Programmation Python',
                'filiere': filiere.nom,
                'description': 'Introduction à la programmation avec Python',
                'university': universite.nom,
            },
            {
                'nom': 'Base de Données',
                'filiere': filiere.nom,
                'description': 'Conception et gestion de bases de données relationnelles',
                'university': universite.nom,
            },
            {
                'nom': 'Algorithmique',
                'filiere': filiere.nom,
                'description': 'Structures de données et algorithmes fondamentaux',
                'university': universite.nom,
            },
            {
                'nom': 'Réseaux Informatiques',
                'filiere': filiere.nom,
                'description': 'Principes des réseaux et protocoles de communication',
                'university': universite.nom,
            },
        ]
        
        created_count = 0
        for cours_data in cours_test:
            # Vérifier si le cours existe déjà
            if not Course.objects.filter(nom=cours_data['nom'], university=cours_data['university']).exists():
                course = Course.objects.create(**cours_data)
                print(f"✅ Cours créé: {course.nom}")
                created_count += 1
            else:
                print(f"⚠️ Cours déjà existant: {cours_data['nom']}")
        
        print(f"\n🎉 {created_count} nouveaux cours créés!")
        
    else:
        print("❌ Pas d'université ou de filière disponible")
        print("💡 Vous devez d'abord créer des universités et filières")
        
        # Créer une université et filière de base si elles n'existent pas
        if not universites.exists():
            print("\n📚 Création d'une université de test...")
            universite = Universite.objects.create(
                nom="Université de Test",
                adresse="123 Rue de l'Éducation, Ville Test"
            )
            print(f"✅ Université créée: {universite.nom}")
        else:
            universite = universites.first()
            
        if not filieres.exists():
            print("\n📖 Création d'une filière de test...")
            filiere = Filiere.objects.create(
                nom="Informatique",
                description="Filière d'informatique générale"
            )
            print(f"✅ Filière créée: {filiere.nom}")
        else:
            filiere = filieres.first()
        
        # Maintenant créer les cours
        print("\n📝 Création des cours...")
        cours_test = [
            {
                'nom': 'Mathématiques Générales',
                'filiere': filiere.nom,
                'description': 'Cours de mathématiques de base couvrant l\'algèbre et l\'analyse',
                'university': universite.nom,
            },
            {
                'nom': 'Programmation Python',
                'filiere': filiere.nom,
                'description': 'Introduction à la programmation avec Python',
                'university': universite.nom,
            },
            {
                'nom': 'Base de Données',
                'filiere': filiere.nom,
                'description': 'Conception et gestion de bases de données relationnelles',
                'university': universite.nom,
            },
            {
                'nom': 'Algorithmique',
                'filiere': filiere.nom,
                'description': 'Structures de données et algorithmes fondamentaux',
                'university': universite.nom,
            },
            {
                'nom': 'Réseaux Informatiques',
                'filiere': filiere.nom,
                'description': 'Principes des réseaux et protocoles de communication',
                'university': universite.nom,
            },
        ]
        
        for cours_data in cours_test:
            course = Course.objects.create(**cours_data)
            print(f"✅ Cours créé: {course.nom}")
    
    # 4. Vérifier les cours créés
    print("\n4. Vérification finale...")
    all_courses = Course.objects.all()
    print(f"Total des cours: {all_courses.count()}")
    for course in all_courses:
        print(f"  - {course.nom} ({course.filiere}) - {course.university}")
    
    print(f"\n🎉 Création terminée! {all_courses.count()} cours disponibles.")

if __name__ == "__main__":
    create_test_courses()