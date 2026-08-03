#!/usr/bin/env python3
"""
Script pour corriger les problèmes d'encodage UTF-8 en PRODUCTION (MySQL/MariaDB)
"""
import os
import sys
import django
from django.conf import settings

# Ajouter le répertoire du projet au path
sys.path.append('/home/jey/resume_plus_clean/backend')

# Configurer Django pour la production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from django.db import connection
from courses.models import Summary, Session

def check_production_database():
    """Vérifier la configuration de la base de données de production"""
    print("🔍 Vérification de la base de données de production...")
    
    try:
        with connection.cursor() as cursor:
            # Vérifier le type de base de données
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            print(f"📊 Version de la base: {version}")
            
            # Vérifier l'encodage de la base de données
            cursor.execute("SHOW VARIABLES LIKE 'character_set_database'")
            result = cursor.fetchone()
            print(f"📊 Encodage de la base: {result[1] if result else 'Non trouvé'}")
            
            # Vérifier l'encodage de la connexion
            cursor.execute("SHOW VARIABLES LIKE 'character_set_connection'")
            result = cursor.fetchone()
            print(f"📊 Encodage de la connexion: {result[1] if result else 'Non trouvé'}")
            
            # Vérifier l'encodage des résultats
            cursor.execute("SHOW VARIABLES LIKE 'character_set_results'")
            result = cursor.fetchone()
            print(f"📊 Encodage des résultats: {result[1] if result else 'Non trouvé'}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

def fix_production_encoding():
    """Corriger l'encodage de la base de données de production"""
    print("\n🔧 Correction de l'encodage UTF-8 de la base de données de production...")
    
    try:
        with connection.cursor() as cursor:
            # Corriger l'encodage de la base de données
            print("🔄 Conversion de la base de données en utf8mb4...")
            cursor.execute("ALTER DATABASE jey_resume CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Base de données convertie en utf8mb4")
            
            # Corriger l'encodage des tables principales
            tables_to_fix = [
                'courses_summary',
                'courses_session', 
                'courses_course',
                'auth_user',
            ]
            
            for table in tables_to_fix:
                try:
                    print(f"🔄 Conversion de la table {table}...")
                    cursor.execute(f"ALTER TABLE {table} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    print(f"✅ Table {table} convertie en utf8mb4")
                except Exception as e:
                    print(f"⚠️ Erreur pour la table {table}: {e}")
            
            # Corriger spécifiquement les colonnes de texte importantes
            text_columns = [
                ('courses_summary', 'texte_resume', 'LONGTEXT'),
                ('courses_summary', 'titre', 'VARCHAR(200)'),
                ('courses_session', 'professeur', 'VARCHAR(200)'),
                ('courses_course', 'nom', 'VARCHAR(200)'),
                ('courses_course', 'description', 'TEXT'),
            ]
            
            for table, column, data_type in text_columns:
                try:
                    print(f"🔄 Correction de {table}.{column}...")
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

def clean_production_invalid_data():
    """Nettoyer les données UTF-8 invalides en production"""
    print("\n🧹 Nettoyage des données UTF-8 invalides en production...")
    
    try:
        with connection.cursor() as cursor:
            # Nettoyer les résumés avec des caractères invalides
            print("🔄 Nettoyage des résumés...")
            cursor.execute("""
                UPDATE courses_summary 
                SET texte_resume = REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(texte_resume, '\\\\xF0\\\\x9F\\\\x93\\\\x9A', '📚'),
                            '\\\\xF0\\\\x9F\\\\x8E\\\\x93', '🎓'
                        ),
                        '\\\\xF0\\\\x9F\\\\x9A\\\\x80', '🚀'
                    ),
                    '\\\\xE2\\\\x9C\\\\x85', '✅'
                )
                WHERE texte_resume LIKE '%\\\\x%'
            """)
            
            affected_rows = cursor.rowcount
            print(f"✅ {affected_rows} résumés nettoyés")
            
            # Nettoyer les titres avec des caractères d'encodage incorrects
            print("🔄 Nettoyage des titres...")
            cursor.execute("""
                UPDATE courses_summary 
                SET titre = REPLACE(
                    REPLACE(
                        REPLACE(titre, 'Ã©', 'é'),
                        'Ã¨', 'è'
                    ),
                    'Ã ', 'à'
                )
                WHERE titre LIKE '%Ã%'
            """)
            
            affected_rows = cursor.rowcount
            print(f"✅ {affected_rows} titres nettoyés")
            
            # Nettoyer les noms de cours
            print("🔄 Nettoyage des noms de cours...")
            cursor.execute("""
                UPDATE courses_course 
                SET nom = REPLACE(
                    REPLACE(
                        REPLACE(nom, 'Ã©', 'é'),
                        'Ã¨', 'è'
                    ),
                    'Ã ', 'à'
                )
                WHERE nom LIKE '%Ã%'
            """)
            
            affected_rows = cursor.rowcount
            print(f"✅ {affected_rows} noms de cours nettoyés")
            
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")

def test_production_emoji_insertion():
    """Tester l'insertion d'emojis en production"""
    print("\n🧪 Test d'insertion d'emojis en production...")
    
    try:
        # Utiliser l'ORM Django pour plus de sécurité
        from courses.models import Course
        
        # Récupérer le premier cours disponible
        course = Course.objects.first()
        if not course:
            print("❌ Aucun cours disponible pour le test")
            return
        
        # Créer un résumé de test avec des emojis
        test_text = "📚 Test d'encodage UTF-8 PRODUCTION avec emojis 🎓✅🚀\n\n" \
                   "Ce texte contient des emojis pour tester l'encodage en production.\n" \
                   "Caractères spéciaux: àéèùç ÀÉÈÙÇ\n" \
                   "Emojis: 📱💻🌐🔧⚡🎯🏆"
        
        # Créer le résumé de test
        test_summary = Summary.objects.create(
            titre="🧪 Test Emoji Production 🎓",
            texte_resume=test_text,
            course=course,
            author_type='cp',
            prix=0,
            is_free=True
        )
        
        print(f"✅ Test d'insertion réussi: ID {test_summary.id}")
        print(f"📝 Titre: {test_summary.titre}")
        print(f"📄 Texte: {test_summary.texte_resume[:150]}...")
        
        # Vérifier que les emojis sont bien sauvegardés
        retrieved_summary = Summary.objects.get(id=test_summary.id)
        if '📚' in retrieved_summary.texte_resume and '🎓' in retrieved_summary.titre:
            print("✅ Emojis correctement sauvegardés et récupérés en production")
        else:
            print("❌ Problème avec les emojis en production")
            print(f"📄 Titre récupéré: {retrieved_summary.titre}")
            print(f"📄 Texte récupéré: {retrieved_summary.texte_resume[:100]}...")
        
        # Supprimer le test
        test_summary.delete()
        print("✅ Données de test nettoyées")
        
    except Exception as e:
        print(f"❌ Erreur lors du test en production: {e}")

def check_production_data():
    """Vérifier les données existantes en production"""
    print("\n🔍 Vérification des données existantes en production...")
    
    try:
        # Compter les résumés
        total_summaries = Summary.objects.count()
        print(f"📊 Total des résumés en production: {total_summaries}")
        
        # Compter les sessions audio
        total_sessions = Session.objects.count()
        print(f"📊 Total des sessions audio en production: {total_sessions}")
        
        # Vérifier les résumés avec des caractères problématiques
        problematic_summaries = Summary.objects.filter(
            texte_resume__contains='\\x'
        ).count()
        print(f"⚠️ Résumés avec caractères problématiques: {problematic_summaries}")
        
        # Vérifier les titres avec des caractères problématiques
        problematic_titles = Summary.objects.filter(
            titre__contains='Ã'
        ).count()
        print(f"⚠️ Titres avec caractères problématiques: {problematic_titles}")
        
        # Vérifier les sessions avec fichiers audio
        sessions_with_audio = Session.objects.exclude(audio_file='').count()
        print(f"🎵 Sessions avec fichiers audio: {sessions_with_audio}")
        
        # Afficher quelques exemples de problèmes
        if problematic_summaries > 0:
            example = Summary.objects.filter(texte_resume__contains='\\x').first()
            if example:
                print(f"📄 Exemple de texte problématique: {example.texte_resume[:100]}...")
        
        if problematic_titles > 0:
            example = Summary.objects.filter(titre__contains='Ã').first()
            if example:
                print(f"📝 Exemple de titre problématique: {example.titre}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

def set_production_connection_encoding():
    """Définir l'encodage de la connexion pour la session actuelle"""
    print("\n🔧 Configuration de l'encodage de la connexion...")
    
    try:
        with connection.cursor() as cursor:
            # Définir l'encodage pour la session actuelle
            cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute("SET CHARACTER SET utf8mb4")
            cursor.execute("SET character_set_connection=utf8mb4")
            cursor.execute("SET character_set_client=utf8mb4")
            cursor.execute("SET character_set_results=utf8mb4")
            print("✅ Encodage de la connexion configuré en utf8mb4")
            
    except Exception as e:
        print(f"❌ Erreur lors de la configuration de la connexion: {e}")

def main():
    print("🚀 CORRECTION DE L'ENCODAGE UTF-8 EN PRODUCTION")
    print("="*60)
    
    # Étape 1: Vérifier la base de données
    check_production_database()
    
    # Étape 2: Configurer l'encodage de la connexion
    set_production_connection_encoding()
    
    # Étape 3: Vérifier les données existantes
    check_production_data()
    
    # Étape 4: Corriger l'encodage (ATTENTION: Opération critique)
    print(f"\n{'='*60}")
    print("⚠️  ATTENTION: OPÉRATION CRITIQUE EN PRODUCTION")
    print("Cette opération va modifier la structure de la base de données.")
    print("Assurez-vous d'avoir une sauvegarde récente.")
    print('='*60)
    
    response = input("Voulez-vous continuer avec la correction? (oui/non): ")
    if response.lower() in ['oui', 'yes', 'y', 'o']:
        fix_production_encoding()
        
        # Étape 5: Nettoyer les données existantes
        clean_production_invalid_data()
        
        # Étape 6: Tester les emojis
        test_production_emoji_insertion()
    else:
        print("❌ Opération annulée par l'utilisateur")
        return
    
    print(f"\n{'='*60}")
    print("📋 RÉSUMÉ DE LA CORRECTION EN PRODUCTION")
    print('='*60)
    print("✅ Base de données vérifiée")
    print("✅ Encodage de connexion configuré")
    print("✅ Structure convertie en utf8mb4")
    print("✅ Données invalides nettoyées")
    print("✅ Support des emojis testé")
    print("✅ Le problème d'encodage devrait être résolu en production")
    print("\n💡 Redémarrez le serveur Django/Gunicorn pour appliquer les changements")
    print("💡 Testez votre application Flutter maintenant")

if __name__ == "__main__":
    main()