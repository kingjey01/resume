#!/usr/bin/env python3
"""
Script de test pour les fonctionnalités audio
"""

import requests
import json
import os

# Configuration
BASE_URL = "https://resumecours.gestionhospitaliare.site/api/courses"
# BASE_URL = "http://localhost:8000/api/courses"  # Pour les tests locaux

def test_audio_endpoints():
    """Teste tous les endpoints audio"""
    
    print("🎵 Test des fonctionnalités audio")
    print("=" * 50)
    
    # 1. Test de récupération des sessions audio
    print("\n1. 📋 Test: Récupération des sessions audio")
    try:
        response = requests.get(f"{BASE_URL}/sessions/audio/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {data.get('count', 0)} sessions audio trouvées")
            
            # Afficher quelques détails
            for session in data.get('sessions', [])[:3]:
                print(f"   📁 Session: {session.get('course_name')} - {session.get('professeur')}")
                if session.get('audio_info'):
                    audio_info = session['audio_info']
                    print(f"      🎵 Fichier: {audio_info.get('file_size_mb', 0)}MB - {audio_info.get('duration_formatted', 'Durée inconnue')}")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
    
    # 2. Test des statistiques de traitement
    print("\n2. 📊 Test: Statistiques de traitement audio")
    try:
        response = requests.get(f"{BASE_URL}/sessions/audio/stats/")
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            print(f"   ✅ Sessions audio totales: {stats.get('total_audio_sessions', 0)}")
            print(f"   ✅ Sessions traitées: {stats.get('processed_sessions', 0)}")
            print(f"   ✅ Sessions en attente: {stats.get('pending_sessions', 0)}")
            print(f"   ✅ Taux de traitement: {stats.get('processing_rate', 0)}%")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
    
    # 3. Test de récupération d'un fichier audio spécifique
    print("\n3. 🎵 Test: Récupération d'un fichier audio")
    try:
        # D'abord récupérer une session avec audio
        response = requests.get(f"{BASE_URL}/sessions/audio/")
        if response.status_code == 200:
            sessions = response.json().get('sessions', [])
            if sessions:
                session_id = sessions[0]['id']
                
                # Tester la récupération du fichier audio
                audio_response = requests.get(f"{BASE_URL}/sessions/{session_id}/audio-file/")
                if audio_response.status_code == 200:
                    audio_data = audio_response.json()
                    print(f"   ✅ Fichier audio accessible: {audio_data.get('file_info', {}).get('name')}")
                    print(f"   🔗 URL: {audio_data.get('audio_url', 'Non disponible')}")
                else:
                    print(f"   ❌ Erreur récupération audio: {audio_response.status_code}")
            else:
                print("   ⚠️ Aucune session audio disponible pour le test")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
    
    # 4. Test des cours disponibles
    print("\n4. 📚 Test: Cours disponibles")
    try:
        response = requests.get(f"{BASE_URL}/courses/")
        if response.status_code == 200:
            courses = response.json()
            if isinstance(courses, list):
                print(f"   ✅ {len(courses)} cours disponibles")
                for course in courses[:3]:
                    print(f"   📖 {course.get('nom')} - {course.get('filiere')}")
            else:
                print(f"   ✅ Cours trouvés (format paginé)")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
    
    # 5. Test des résumés
    print("\n5. 📝 Test: Résumés disponibles")
    try:
        response = requests.get(f"{BASE_URL}/summaries/")
        if response.status_code == 200:
            summaries = response.json()
            if isinstance(summaries, list):
                print(f"   ✅ {len(summaries)} résumés disponibles")
                
                # Compter par type
                cp_count = sum(1 for s in summaries if s.get('author_type') == 'cp')
                ai_count = sum(1 for s in summaries if s.get('author_type') == 'ai')
                print(f"   👨‍🏫 Résumés par CP: {cp_count}")
                print(f"   🤖 Résumés par IA: {ai_count}")
            else:
                print(f"   ✅ Résumés trouvés (format paginé)")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Tests terminés")
    print("\n💡 Pour tester l'upload audio, utilisez l'interface web ou:")
    print("   curl -X POST -F 'audio_file=@fichier.mp3' -F 'course_id=1' \\")
    print(f"        {BASE_URL}/sessions/upload-audio/")

def test_database_content():
    """Teste le contenu de la base de données directement"""
    print("\n🔍 Test du contenu de la base de données")
    print("=" * 50)
    
    try:
        import pymysql
        
        connection = pymysql.connect(
            host='localhost',
            user='jey_resume',
            password='1234',
            database='jey_resume',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Vérifier les sessions avec audio
        cursor.execute("""
            SELECT s.id, s.professeur, c.nom as course_name, s.audio_file, s.date
            FROM courses_session s
            JOIN courses_course c ON s.course_id = c.id
            WHERE s.audio_file IS NOT NULL AND s.audio_file != ''
            ORDER BY s.created_at DESC
            LIMIT 5
        """)
        
        sessions = cursor.fetchall()
        print(f"\n📁 Sessions avec fichiers audio: {len(sessions)}")
        for session in sessions:
            print(f"   🎵 ID {session[0]}: {session[2]} par {session[1]}")
            print(f"      📄 Fichier: {session[3]}")
        
        # Vérifier les résumés IA
        cursor.execute("""
            SELECT s.id, s.titre, s.author_type, c.nom as course_name
            FROM courses_summary s
            JOIN courses_course c ON s.course_id = c.id
            WHERE s.author_type = 'ai'
            ORDER BY s.created_at DESC
            LIMIT 5
        """)
        
        ai_summaries = cursor.fetchall()
        print(f"\n🤖 Résumés générés par IA: {len(ai_summaries)}")
        for summary in ai_summaries:
            print(f"   📝 {summary[1]} - {summary[3]}")
        
        connection.close()
        print("\n✅ Test base de données terminé")
        
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")

if __name__ == '__main__':
    print("🚀 Démarrage des tests audio Resume+")
    
    # Test des endpoints API
    test_audio_endpoints()
    
    # Test de la base de données
    test_database_content()
    
    print("\n🎯 Tests terminés!")
    print("\n📋 Prochaines étapes:")
    print("1. Vérifiez que le serveur web fonctionne")
    print("2. Testez l'upload d'un fichier audio via l'interface")
    print("3. Vérifiez la génération automatique de résumés")
    print("4. Testez la lecture audio dans l'application Flutter")