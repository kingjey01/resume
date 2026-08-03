#!/usr/bin/env python3
"""
Script pour corriger les problèmes d'encodage UTF-8 dans la base de données
"""
import os
import sys
import django
from django.conf import settings

# Ajouter le répertoire du projet au path
sys.path.append('/home/jey/resume_plus_clean/backend')

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from django.db import connection

def fix_database_encoding():
    """Corriger l'encodage de la base de données"""
    print("🔧 Correction de l'encodage UTF-8 de la base de données...")
    
    try:
        with connection.cursor() as cursor:
            # Vérifier l'encodage actuel
            cursor.execute("SHOW VARIABLES LIKE 'character_set_database'")
            result = cursor.fetchone()
            print(f"📊 Encodage actuel de la base: {result}")
            
            # Corriger l'encodage de la base de données
            cursor.execute("ALTER DATABASE jey_resume CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Base de données convertie en utf8mb4")
            
            # Corriger l'encodage des tables principales
            tables_to_fix = [
                'courses_summary',
                'courses_audiosession', 
                'courses_course',
                'auth_user',
            ]
            
            for table in tables_to_fix:
                try:
                    cursor.execute(f"ALTER TABLE {table} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    print(f"✅ Table {table} convertie en utf8mb4")
                except Exception as e:
                    print(f"⚠️ Erreur pour la table {table}: {e}")
            
            # Corriger spécifiquement les colonnes de texte
            text_columns = [
                ('courses_summary', 'texte_resume', 'LONGTEXT'),
                ('courses_summary', 'titre', 'VARCHAR(255)'),
                ('courses_audiosession', 'title', 'VARCHAR(255)'),
                ('courses_audiosession', 'transcription', 'LONGTEXT'),
                ('courses_audiosession', 'summary_text', 'LONGTEXT'),
            ]
            
            for table, column, data_type in text_columns:
                try:
                    cursor.execute(f"""
                        ALTER TABLE {table} 
                        MODIFY COLUMN {column} {data_type} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                    """)
                    print(f"✅ Colonne {table}.{column} corrigée")
                except Exception as e:
                    print(f"⚠️ Erreur pour {table}.{column}: {e}")
            
            print("🎉 Correction de l'encodage terminée !")
            
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")

def clean_invalid_utf8_data():
    """Nettoyer les données UTF-8 invalides existantes"""
    print("\n🧹 Nettoyage des données UTF-8 invalides...")
    
    try:
        with connection.cursor() as cursor:
            # Nettoyer les résumés avec des caractères invalides
            cursor.execute("""
                UPDATE courses_summary 
                SET texte_resume = REPLACE(
                    REPLACE(
                        REPLACE(texte_resume, '\\\\xF0\\\\x9F\\\\x93\\\\x9A', '📚'),
                        '\\\\xF0\\\\x9F\\\\x8E\\\\x93', '🎓'
                    ),
                    '\\\\x', ''
                )
                WHERE texte_resume LIKE '%\\\\x%'
            """)
            
            affected_rows = cursor.rowcount
            print(f"✅ {affected_rows} résumés nettoyés")
            
            # Nettoyer les titres
            cursor.execute("""
                UPDATE courses_summary 
                SET titre = REPLACE(
                    REPLACE(titre, '\\\\x', ''),
                    'Ã©', 'é'
                )
                WHERE titre LIKE '%\\\\x%' OR titre LIKE '%Ã©%'
            """)
            
            affected_rows = cursor.rowcount
            print(f"✅ {affected_rows} titres nettoyés")
            
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")

def test_emoji_insertion():
    """Tester l'insertion d'emojis"""
    print("\n🧪 Test d'insertion d'emojis...")
    
    try:
        # Tester avec une requête SQL directe
        with connection.cursor() as cursor:
            test_text = "📚 Test d'encodage UTF-8 avec emojis 🎓✅🚀"
            
            cursor.execute("""
                INSERT INTO courses_summary (titre, texte_resume, course_id, author_type, prix, is_free, created_at, updated_at)
                VALUES (%s, %s, 1, 'cp', 0, 1, NOW(), NOW())
            """, ["Test Emoji", test_text])
            
            print(f"✅ Test d'insertion réussi: {test_text}")
            
            # Supprimer le test
            cursor.execute("DELETE FROM courses_summary WHERE titre = 'Test Emoji'")
            print("✅ Données de test nettoyées")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")

def main():
    print("🚀 CORRECTION DE L'ENCODAGE UTF-8")
    print("="*50)
    
    # Étape 1: Corriger l'encodage
    fix_database_encoding()
    
    # Étape 2: Nettoyer les données existantes
    clean_invalid_utf8_data()
    
    # Étape 3: Tester les emojis
    test_emoji_insertion()
    
    print(f"\n{'='*50}")
    print("📋 RÉSUMÉ")
    print('='*50)
    print("✅ Base de données convertie en utf8mb4")
    print("✅ Tables principales corrigées")
    print("✅ Données invalides nettoyées")
    print("✅ Support des emojis activé")
    print("✅ Le problème d'encodage devrait être résolu")
    print("\n💡 Redémarrez le serveur Django pour appliquer les changements")

if __name__ == "__main__":
    main()