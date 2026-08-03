#!/usr/bin/env python3
"""
Test d'upload audio simplifié
"""
import requests
import json
import io
import wave
import struct
import random

BASE_URL = "https://resumecours.gestionhospitaliare.site"
TOKEN = "9743c81fdd50b11c38a55fb9de24c56d8d4857dd"  # Token admin (Token Authentication)

def create_simple_audio_file():
    """Créer un fichier audio WAV simple"""
    print("🎵 Création d'un fichier audio de test...")
    
    # Créer un fichier WAV minimal (1 seconde de silence)
    sample_rate = 8000  # Fréquence réduite
    duration = 1  # 1 seconde
    
    # Générer des échantillons (silence avec un peu de bruit)
    frames = []
    for i in range(sample_rate * duration):
        # Petit bruit aléatoire pour simuler un vrai enregistrement
        noise = random.randint(-100, 100)
        frames.append(struct.pack('<h', noise))
    
    # Créer le fichier WAV en mémoire
    audio_buffer = io.BytesIO()
    with wave.open(audio_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(frames))
    
    audio_buffer.seek(0)
    file_size = len(audio_buffer.getvalue())
    print(f"✅ Fichier audio créé: {file_size} bytes ({file_size/1024:.1f} KB)")
    return audio_buffer

def test_simple_endpoints():
    """Test des endpoints simples d'abord"""
    print("🔍 Test des endpoints de base...")
    
    headers = {
        'Authorization': f'Token {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    endpoints = [
        ("/api/", "API Root"),
        ("/api/sessions/", "Sessions"),
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
            print(f"  {name:<15} → {response.status_code}")
            
            if response.status_code == 500:
                print(f"    ❌ Erreur serveur 500")
            elif response.status_code == 200:
                print(f"    ✅ OK")
                
        except Exception as e:
            print(f"  {name:<15} → ERROR: {e}")

def test_audio_upload_direct():
    """Test d'upload audio direct avec un course_id fixe"""
    print(f"\n🎤 Test d'upload audio direct...")
    
    # Créer le fichier audio
    audio_file = create_simple_audio_file()
    
    # Utiliser un course_id qui existe probablement (1)
    course_id = 1
    
    # Préparer les données
    headers = {
        'Authorization': f'Token {TOKEN}',
    }
    
    # Données du formulaire
    data = {
        'course_id': str(course_id),
        'title': f'Test Audio Upload {random.randint(1000, 9999)}',
        'auto_process': 'false'  # Désactiver le traitement IA pour éviter les erreurs
    }
    
    # Fichier audio
    files = {
        'audio_file': ('test_recording.wav', audio_file, 'audio/wav')
    }
    
    try:
        print("📤 Upload en cours...")
        print(f"📊 Données: {data}")
        print(f"📁 Fichier: test_recording.wav ({len(audio_file.getvalue())} bytes)")
        
        response = requests.post(
            f"{BASE_URL}/api/courses/sessions/upload-audio/",
            data=data,
            files=files,
            headers=headers,
            timeout=30
        )
        
        print(f"📡 Réponse: {response.status_code}")
        
        if response.status_code == 201:
            try:
                result = response.json()
                print("✅ Upload réussi!")
                print(f"📄 Réponse: {json.dumps(result, indent=2)}")
                return True
            except:
                print("✅ Upload réussi (réponse non-JSON)")
                print(f"📄 Contenu: {response.text[:300]}")
                return True
                
        elif response.status_code == 400:
            print(f"❌ Erreur de données: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📄 Erreurs: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📄 Contenu: {response.text[:500]}")
                
        elif response.status_code == 500:
            print(f"❌ Erreur serveur: {response.status_code}")
            print(f"📄 Contenu: {response.text[:500]}")
            
        else:
            print(f"❌ Échec upload: {response.status_code}")
            print(f"📄 Contenu: {response.text[:500]}")
                
    except Exception as e:
        print(f"❌ Erreur upload: {e}")
    
    return False

def test_with_different_course_ids():
    """Test avec différents course_id"""
    print(f"\n🔄 Test avec différents course_id...")
    
    course_ids = [1, 2, 3]  # Tester plusieurs IDs
    
    for course_id in course_ids:
        print(f"\n📚 Test avec course_id = {course_id}")
        
        # Créer un nouveau fichier pour chaque test
        audio_file = create_simple_audio_file()
        
        headers = {'Authorization': f'Token {TOKEN}'}
        data = {
            'course_id': str(course_id),
            'title': f'Test Course {course_id}',
            'auto_process': 'false'
        }
        files = {
            'audio_file': ('test_recording.wav', audio_file, 'audio/wav')
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/courses/sessions/upload-audio/",
                data=data,
                files=files,
                headers=headers,
                timeout=15
            )
            
            print(f"  📡 Réponse: {response.status_code}")
            
            if response.status_code == 201:
                print(f"  ✅ Succès avec course_id {course_id}!")
                return True
            elif response.status_code == 404:
                print(f"  ❌ Course {course_id} non trouvé")
            elif response.status_code == 400:
                print(f"  ❌ Données invalides")
                try:
                    error = response.json()
                    print(f"    📄 {error}")
                except:
                    pass
            else:
                print(f"  ❌ Erreur {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
    
    return False

def main():
    print("🚀 TEST SIMPLIFIÉ D'UPLOAD AUDIO")
    print("="*50)
    
    # Test 1: Endpoints de base
    test_simple_endpoints()
    
    # Test 2: Upload direct
    success = test_audio_upload_direct()
    
    # Test 3: Si échec, tester avec différents course_id
    if not success:
        success = test_with_different_course_ids()
    
    print(f"\n{'='*50}")
    print("📋 RÉSUMÉ")
    print('='*50)
    
    if success:
        print("✅ Upload audio RÉUSSI!")
        print("✅ Les permissions fonctionnent!")
        print("✅ Votre app Flutter devrait maintenant marcher!")
    else:
        print("❌ Upload audio ÉCHOUÉ")
        print("❌ Vérifiez les logs du serveur")
        print("❌ Peut-être un problème de course_id ou de configuration")

if __name__ == "__main__":
    main()