#!/usr/bin/env python3
"""
Vérifier l'encodage de la base de données MySQL
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection

def check_database_encoding():
    """Vérifier l'encodage de la base de données"""
    print("🔍 Vérification de l'encodage de la base de données...")
    
    with connection.cursor() as cursor:
        # Vérifier l'encodage de la base de données
        cursor.execute("SELECT @@character_set_database, @@collation_database")
        db_charset, db_collation = cursor.fetchone()
        print(f"📊 Base de données:")
        print(f"  Charset: {db_charset}")
        print(f"  Collation: {db_collation}")
        
        # Vérifier l'encodage de la connexion
        cursor.execute("SELECT @@character_set_connection, @@collation_connection")
        conn_charset, conn_collation = cursor.fetchone()
        print(f"📡 Connexion:")
        print(f"  Charset: {conn_charset}")
        print(f"  Collation: {conn_collation}")
        
        # Vérifier l'encodage de la table courses_summary
        cursor.execute("""
            SELECT COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'jey_resume' 
            AND TABLE_NAME = 'courses_summary' 
            AND DATA_TYPE IN ('varchar', 'text', 'longtext')
        """)
        
        print(f"\n📋 Colonnes de la table courses_summary:")
        for column_name, charset, collation in cursor.fetchall():
            status = "✅" if charset == "utf8mb4" else "❌"
            print(f"  {status} {column_name}: {charset} ({collation})")
        
        # Vérifier les variables système importantes
        cursor.execute("""
            SHOW VARIABLES WHERE Variable_name IN (
                'character_set_server',
                'character_set_database', 
                'character_set_connection',
                'character_set_client',
                'character_set_results'
            )
        """)
        
        print(f"\n⚙️  Variables système:")
        for var_name, var_value in cursor.fetchall():
            status = "✅" if var_value == "utf8mb4" else "❌"
            print(f"  {status} {var_name}: {var_value}")

def generate_fix_sql():
    """Générer les commandes SQL pour corriger l'encodage"""
    print(f"\n🔧 COMMANDES SQL POUR CORRIGER L'ENCODAGE:")
    print("="*60)
    
    sql_commands = [
        "-- 1. Modifier la base de données",
        "ALTER DATABASE jey_resume CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        "",
        "-- 2. Modifier la table courses_summary",
        "ALTER TABLE courses_summary CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        "",
        "-- 3. Modifier spécifiquement la colonne texte_resume",
        "ALTER TABLE courses_summary MODIFY COLUMN texte_resume LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        "",
        "-- 4. Vérifier d'autres tables importantes",
        "ALTER TABLE users_userprofile CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        "ALTER TABLE courses_course CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        "ALTER TABLE courses_session CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
    ]
    
    for cmd in sql_commands:
        print(cmd)

if __name__ == "__main__":
    print("🚀 DIAGNOSTIC D'ENCODAGE DE LA BASE DE DONNÉES")
    print("="*60)
    
    try:
        check_database_encoding()
        generate_fix_sql()
        
        print(f"\n{'='*60}")
        print("📋 ACTIONS RECOMMANDÉES:")
        print("1. Exécutez les commandes SQL ci-dessus sur votre serveur MySQL")
        print("2. Redémarrez Apache: sudo systemctl restart httpd")
        print("3. Testez à nouveau la création de summaries")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()