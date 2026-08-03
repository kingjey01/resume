#!/usr/bin/env python3
"""
Script de test pour vérifier la création des données
"""

import pymysql

def test_database_content():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='jey_resume',
            password='1234',
            database='jey_resume',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        print("🔍 Vérification du contenu de la base de données")
        print("=" * 50)
        
        # Vérifier les tables principales
        tables_to_check = [
            ('courses_universite', 'Universités'),
            ('courses_filiere', 'Filières'),
            ('courses_promotion', 'Promotions'),
            ('courses_course', 'Cours'),
            ('courses_summary', 'Résumés'),
            ('courses_audiosession', 'Séances Audio'),
            ('auth_user', 'Utilisateurs'),
            ('users_userprofile', 'Profils Utilisateurs')
        ]
        
        for table_name, display_name in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  ✓ {display_name}: {count} enregistrements")
                
                # Afficher quelques exemples pour certaines tables
                if table_name == 'courses_course' and count > 0:
                    cursor.execute(f"SELECT nom FROM {table_name} LIMIT 3")
                    courses = cursor.fetchall()
                    for course in courses:
                        print(f"    - {course[0]}")
                        
                elif table_name == 'courses_summary' and count > 0:
                    cursor.execute(f"SELECT title, summary_type FROM {table_name} LIMIT 3")
                    summaries = cursor.fetchall()
                    for summary in summaries:
                        print(f"    - {summary[0]} ({summary[1]})")
                        
                elif table_name == 'courses_audiosession' and count > 0:
                    cursor.execute(f"SELECT title, status FROM {table_name} LIMIT 3")
                    sessions = cursor.fetchall()
                    for session in sessions:
                        print(f"    - {session[0]} ({session[1]})")
                        
            except pymysql.Error as e:
                print(f"  ⚠ Erreur pour {display_name}: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Vérification terminée")
        
    except pymysql.Error as e:
        print(f"❌ Erreur de connexion: {e}")
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    test_database_content()