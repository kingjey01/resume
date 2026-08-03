#!/usr/bin/env python3
"""
Version ultra-simple pour créer des données de test
"""

import pymysql

# Connexion directe à MySQL
try:
    connection = pymysql.connect(
        host='localhost',
        user='jey_resume',
        password='1234',
        database='jey_resume',
        charset='utf8mb4'
    )
    
    cursor = connection.cursor()
    
    print("✅ Connexion MySQL réussie")
    print("🌱 Création des données de test...")
    
    # Créer les universités
    universites = [
        ('Université de Kinshasa', 'Kinshasa, RDC'),
        ('Université de Lubumbashi', 'Lubumbashi, RDC'),
        ('Université de Kisangani', 'Kisangani, RDC'),
    ]
    
    for nom, adresse in universites:
        try:
            cursor.execute(
                "INSERT IGNORE INTO courses_universite (nom, adresse) VALUES (%s, %s)",
                (nom, adresse)
            )
            print(f"  ✓ Université: {nom}")
        except Exception as e:
            print(f"  ⚠ Erreur université {nom}: {e}")
    
    # Créer les filières
    filieres = [
        ('Informatique', 'Sciences Informatiques et Technologies'),
        ('Médecine', 'Sciences Médicales'),
        ('Droit', 'Sciences Juridiques'),
    ]
    
    for nom, description in filieres:
        try:
            cursor.execute(
                "INSERT IGNORE INTO courses_filiere (nom, description) VALUES (%s, %s)",
                (nom, description)
            )
            print(f"  ✓ Filière: {nom}")
        except Exception as e:
            print(f"  ⚠ Erreur filière {nom}: {e}")
    
    # Créer les promotions
    promotions = [
        ('L1', 1),
        ('L2', 2),
        ('L3', 3),
    ]
    
    for nom, annee in promotions:
        try:
            cursor.execute(
                "INSERT IGNORE INTO courses_promotion (nom, annee) VALUES (%s, %s)",
                (nom, annee)
            )
            print(f"  ✓ Promotion: {nom}")
        except Exception as e:
            print(f"  ⚠ Erreur promotion {nom}: {e}")
    
    connection.commit()
    print("\n✅ Données de base créées avec succès!")
    
    # Afficher les statistiques
    cursor.execute("SELECT COUNT(*) FROM courses_universite")
    nb_univ = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM courses_filiere")
    nb_filiere = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM courses_promotion")
    nb_promo = cursor.fetchone()[0]
    
    print(f"\n📊 Statistiques:")
    print(f"  Universités: {nb_univ}")
    print(f"  Filières: {nb_filiere}")
    print(f"  Promotions: {nb_promo}")
    
except pymysql.Error as e:
    print(f"❌ Erreur MySQL: {e}")
except Exception as e:
    print(f"❌ Erreur générale: {e}")
finally:
    if 'connection' in locals():
        connection.close()
        print("\n🔌 Connexion fermée")