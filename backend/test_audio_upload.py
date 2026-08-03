#!/usr/bin/env python3
"""
Test d'upload audio complet - Simulation Flutter
"""
import requests
import json
import io
import wave
import struct
import random

BASE_URL = "https://resumecours.gestionhospitaliare.site"
TOKEN = "9743c81fdd50b11c38a55fb9de24c56d8d4857dd"  # Token admin

def create_fake_audio_file():
    """Créer un faux fichier audio WAV pour le test"""
    print("🎵 Création d'un fichier audio de test...")
    
    # Paramètres audio
    sample_rate = 44100
    duration = 2  # 2 secondes
    frequency = 440  # La note A4
    
    # Générer une onde sinusoïdale
    frames = []
    for i in range(int(sample_rate * duration)):
        # Onde sinusoïdale simple
        value = int(32767 * 0.3 * (
            0.5 * (1 + (i % 1000) / 1000) *  # Variation d'amplitude
            (1 if (i // 5000) % 2 == 0 else -1) *  # Alternance
            (1 if i % 100 < 50 else 0.5)  # Modulation
        ))
        frames.append(struct.pack('<h', value))
    
    # Créer le fichier WAV en mémoire
    audio_buffer = io.BytesIO()
    with wave.open(audio_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(frames))
    
    audio_buffer.seek(0)
    print(f"✅ Fichier audio créé: {len(audio_buffer.getvalue())} bytes")
    return audio_buffer

def test_get_courses():
    """Récupérer la liste des cours pour le test"""
    print("📚 Récupération des cours disponibles...")
    
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/courses/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            courses = []
            
            # Extraire les cours des universités
            for universite in data.get('universites', []):
                for filiere in universite.get('filieres', []):
                    for promotion in filiere.get('promotions', []):
                        for course in promotion.get('courses', []):
                            courses.append({
                                'id': course['id'],
                                'nom': course['nom'],
                                'promotion': promotion['nom']
                            })
            
            print(f"✅ {len(courses)} cours trouvés")
            for course in courses[:3]:  # Afficher les 3 premiers
                print(f"  📖 {course['id']}: {course['nom']} ({course['promotion']})")
            
            return courses[0] if courses else None
        else:
            print(f"❌ Erreur récupération cours: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_audio_upload(course_id):
    """Test d'upload audio complet"""
    print(f"\n🎤 Test d'upload audio pour le cours {course_id}...")
    
    # Créer le fichier audio
    audio_file = create_fake_audio_file()
    
    # Préparer les données
    headers = {
        'Authorization': f'Bearer {TOKEN}',
    }
    
    # Données du formulaire
    data = {
        'course_id': course_id,
        'title': f'Test Enregistrement {random.randint(1000, 9999)}',
        'auto_process': 'true'
    }
    
    # Fichier audio
    files = {
        'audio_file': ('test_recording.wav', audio_file, 'audio/wav')
    }
    
    try:
        print("📤 Upload en cours...")
        response = requests.post(
            f"{BASE_URL}/api/courses/sessions/upload-audio/",
            data=data,
            files=files,
            headers=headers,
            timeout=30
        )
        
        print(f"📡 Réponse: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Upload réussi!")
            print(f"🆔 Session ID: {result.get('session', {}).get('id')}")
            print(f"📚 Cours: {result.get('session', {}).get('course_name')}")
            print(f"👨‍🏫 Professeur: {result.get('session', {}).get('professeur')}")
            print(f"🔗 Fichier audio: {result.get('session', {}).get('audio_file')}")
            
            # Vérifier le traitement IA
            if result.get('ai_processing'):
                ai_result = result['ai_processing']
                if ai_result.get('success'):
                    print(f"🤖 Résumé IA généré: ID {ai_result.get('summary_id')}")
                else:
                    print(f"⚠️ Traitement IA échoué: {ai_result.get('error')}")
            
            return result
        else:
            print(f"❌ Échec upload: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Erreur: {error_data}")
            except:
                print(f"Contenu: {response.text[:500]}")
                
    except Exception as e:
        print(f"❌ Erreur upload: {e}")
    
    return None

def test_get_sessions():
    """Vérifier les sessions créées"""
    print(f"\n📋 Vérification des sessions audio...")
    
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/sessions/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            # La réponse peut être du HTML ou JSON
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                sessions = response.json()
                print(f"✅ {len(sessions)} sessions trouvées")
                
                for session in sessions[-3:]:  # 3 dernières
                    print(f"  🎤 {session.get('id')}: {session.get('professeur')} - {session.get('date', '')[:19]}")
            else:
                print("✅ Sessions endpoint accessible (réponse HTML)")
        else:
            print(f"❌ Erreur sessions: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    print("🚀 TEST COMPLET D'ENREGISTREMENT AUDIO")
    print("="*60)
    
    # Test 1: Récupérer les cours
    course = test_get_courses()
    
    if not course:
        print("❌ Impossible de récupérer les cours - Test arrêté")
        return
    
    # Test 2: Upload audio
    upload_result = test_audio_upload(course['id'])
    
    # Test 3: Vérifier les sessions
    test_get_sessions()
    
    print(f"\n{'='*60}")
    print("📋 RÉSUMÉ DU TEST")
    print('='*60)
    
    if upload_result:
        print("✅ Test d'enregistrement audio RÉUSSI!")
        print("✅ Les permissions sont correctes!")
        print("✅ L'upload fonctionne parfaitement!")
        print("✅ Votre app Flutter devrait maintenant fonctionner!")
    else:
        print("❌ Test d'enregistrement audio ÉCHOUÉ")
        print("❌ Vérifiez les logs du serveur pour plus de détails")

if __name__ == "__main__":
    main()