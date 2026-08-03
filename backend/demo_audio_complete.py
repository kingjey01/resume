#!/usr/bin/env python3
"""
Démo complète pour créer et tester les fonctionnalités audio
"""

import os
import sys
import django
from pathlib import Path
import wave
import struct
import math

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')

try:
    django.setup()
except:
    pass

from courses.models import Session, Course, Summary
from django.core.files.base import ContentFile
from django.contrib.auth.models import User

def create_real_wav_file(filename, duration=5, frequency=440):
    """Créer un vrai fichier WAV avec du son"""
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    
    print(f"🎵 Création du fichier {filename} ({duration}s, {frequency}Hz)")
    
    # Générer les échantillons audio
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        
        # Créer une mélodie simple avec fade in/out
        fade_duration = 0.1  # 100ms de fade
        if t < fade_duration:
            fade = t / fade_duration
        elif t > duration - fade_duration:
            fade = (duration - t) / fade_duration
        else:
            fade = 1.0
        
        # Onde sinusoïdale avec harmoniques
        amplitude = 0.3 * fade
        sample_value = (
            amplitude * math.sin(2 * math.pi * frequency * t) +
            amplitude * 0.3 * math.sin(2 * math.pi * frequency * 2 * t) +
            amplitude * 0.1 * math.sin(2 * math.pi * frequency * 3 * t)
        )
        
        # Convertir en entier 16-bit
        sample_int = int(sample_value * 32767)
        sample_int = max(-32768, min(32767, sample_int))  # Clamp
        samples.append(sample_int)
    
    # Créer le fichier WAV en mémoire
    import io
    wav_buffer = io.BytesIO()
    
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16 bits
        wav_file.setframerate(sample_rate)
        
        # Écrire tous les échantillons
        wav_data = b''.join(struct.pack('<h', sample) for sample in samples)
        wav_file.writeframes(wav_data)
    
    wav_content = wav_buffer.getvalue()
    print(f"  ✅ Fichier créé: {len(wav_content)} bytes")
    return wav_content

def create_demo_sessions_with_audio():
    """Créer des sessions de démonstration avec de vrais fichiers audio"""
    print("🎬 Création de sessions de démonstration avec audio")
    print("=" * 60)
    
    # Vérifier qu'on a des cours
    courses = Course.objects.all()
    if not courses.exists():
        print("❌ Aucun cours trouvé. Créez d'abord des cours avec create_test_data.py")
        return False
    
    # Créer le répertoire media
    media_dir = BASE_DIR / "media" / "audio_sessions"
    media_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Répertoire media: {media_dir}")
    
    # Données des sessions de démonstration
    demo_sessions = [
        {
            'course': courses[0],
            'professeur': 'Prof. Martin Dubois',
            'duration': 8,
            'frequency': 440,  # La
            'title': 'Introduction aux Variables'
        },
        {
            'course': courses[1] if len(courses) > 1 else courses[0],
            'professeur': 'Prof. Sarah Johnson', 
            'duration': 6,
            'frequency': 523,  # Do
            'title': 'Structures de Contrôle'
        },
        {
            'course': courses[2] if len(courses) > 2 else courses[0],
            'professeur': 'Prof. Ahmed Hassan',
            'duration': 10,
            'frequency': 659,  # Mi
            'title': 'Bases de Données'
        }
    ]
    
    created_sessions = []
    
    for i, session_data in enumerate(demo_sessions):
        try:
            # Créer la session
            from django.utils import timezone
            session = Session.objects.create(
                course=session_data['course'],
                date=timezone.now() - timezone.timedelta(days=i+1),
                professeur=session_data['professeur']
            )
            
            # Créer le fichier audio
            filename = f'demo_session_{session.id}_{session_data["title"].lower().replace(" ", "_")}.wav'
            audio_content = create_real_wav_file(
                filename, 
                session_data['duration'], 
                session_data['frequency']
            )
            
            # Sauvegarder le fichier
            session.audio_file.save(
                filename,
                ContentFile(audio_content),
                save=True
            )
            
            created_sessions.append(session)
            print(f"  ✅ Session {session.id}: {session_data['title']}")
            print(f"     📁 Fichier: {session.audio_file.name}")
            print(f"     🎵 Durée: {session_data['duration']}s, Fréquence: {session_data['frequency']}Hz")
            
        except Exception as e:
            print(f"  ❌ Erreur session {i+1}: {e}")
    
    print(f"\n🎯 {len(created_sessions)} sessions créées avec succès")
    return created_sessions

def create_demo_summaries():
    """Créer des résumés de démonstration"""
    print("\n📝 Création de résumés de démonstration")
    print("=" * 60)
    
    sessions_with_audio = Session.objects.filter(audio_file__isnull=False).exclude(audio_file='')
    
    for session in sessions_with_audio[:3]:
        try:
            # Vérifier si un résumé existe déjà
            existing_summary = Summary.objects.filter(session=session, author_type='ai').first()
            if existing_summary:
                print(f"  ℹ️ Résumé IA existe déjà pour session {session.id}")
                continue
            
            # Créer un résumé IA
            summary_text = f"""
🎓 RÉSUMÉ AUTOMATIQUE - {session.course.nom}
👨‍🏫 Professeur: {session.professeur}
📅 Date: {session.date.strftime('%d/%m/%Y')}

📋 CONTENU DE LA SÉANCE:
Cette séance a abordé les concepts fondamentaux de {session.course.nom}.

🔑 POINTS CLÉS:
• Introduction aux concepts de base
• Exemples pratiques et applications
• Exercices et cas d'usage concrets
• Questions-réponses avec les étudiants

💡 RÉSUMÉ:
Le professeur {session.professeur} a présenté de manière claire et structurée 
les éléments essentiels du cours. La séance était interactive avec de nombreux 
exemples pratiques pour faciliter la compréhension.

🎵 INFORMATIONS AUDIO:
• Durée estimée: {session.audio_file.size // 1024 if session.audio_file.size else 'N/A'} KB
• Format: WAV (démonstration)
• Qualité: Audio de test généré automatiquement

⚡ GÉNÉRÉ AUTOMATIQUEMENT
Ce résumé a été créé par l'IA à partir de l'enregistrement audio de la séance.
            """.strip()
            
            summary = Summary.objects.create(
                titre=f"Résumé IA - {session.course.nom} ({session.date.strftime('%d/%m')})",
                texte_resume=summary_text,
                course=session.course,
                session=session,
                author_type='ai',
                prix=0.00,
                is_free=True
            )
            
            print(f"  ✅ Résumé IA créé pour session {session.id}")
            
        except Exception as e:
            print(f"  ❌ Erreur résumé session {session.id}: {e}")

def test_audio_files_locally():
    """Tester les fichiers audio localement"""
    print("\n🧪 Test des fichiers audio localement")
    print("=" * 60)
    
    sessions_with_audio = Session.objects.filter(audio_file__isnull=False).exclude(audio_file='')
    
    if not sessions_with_audio.exists():
        print("❌ Aucune session avec fichier audio trouvée")
        return False
    
    print(f"📊 Sessions avec audio: {sessions_with_audio.count()}")
    
    for session in sessions_with_audio:
        print(f"\n🎵 Session {session.id}: {session.course.nom}")
        print(f"   👨‍🏫 Professeur: {session.professeur}")
        print(f"   📁 Fichier: {session.audio_file.name}")
        
        # Vérifier l'existence du fichier
        try:
            if hasattr(session.audio_file, 'path'):
                file_path = session.audio_file.path
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"   ✅ Fichier existe: {file_size} bytes")
                    
                    # Vérifier que c'est un fichier WAV valide
                    try:
                        with wave.open(file_path, 'rb') as wav_file:
                            frames = wav_file.getnframes()
                            sample_rate = wav_file.getframerate()
                            duration = frames / sample_rate
                            print(f"   🎵 WAV valide: {duration:.1f}s, {sample_rate}Hz")
                    except Exception as e:
                        print(f"   ⚠️ Erreur lecture WAV: {e}")
                else:
                    print(f"   ❌ Fichier n'existe pas: {file_path}")
            else:
                print(f"   ⚠️ Pas de chemin de fichier disponible")
                
            # Tester l'URL
            try:
                url = session.audio_file.url
                print(f"   🔗 URL: {url}")
            except Exception as e:
                print(f"   ❌ Erreur URL: {e}")
                
        except Exception as e:
            print(f"   ❌ Erreur test fichier: {e}")
    
    return True

def create_html_audio_test():
    """Créer une page HTML de test pour les fichiers audio"""
    print("\n🌐 Création d'une page de test HTML")
    print("=" * 60)
    
    sessions_with_audio = Session.objects.filter(audio_file__isnull=False).exclude(audio_file='')
    
    html_content = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Audio Resume+</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .session { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .session h3 { margin-top: 0; color: #333; }
        .audio-player { margin: 10px 0; }
        .info { background: #e8f4fd; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .error { background: #ffe6e6; padding: 10px; border-radius: 5px; margin: 10px 0; color: #d00; }
        .success { background: #e6ffe6; padding: 10px; border-radius: 5px; margin: 10px 0; color: #060; }
        button { background: #007cba; color: white; border: none; padding: 8px 15px; border-radius: 3px; cursor: pointer; }
        button:hover { background: #005a87; }
        .test-results { margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 Test Audio Resume+</h1>
        <div class="info">
            <strong>Instructions:</strong>
            <ul>
                <li>Cliquez sur "Play" pour tester la lecture audio</li>
                <li>Utilisez les contrôles du navigateur pour ajuster le volume</li>
                <li>Vérifiez que chaque fichier se charge et se lit correctement</li>
            </ul>
        </div>
        
        <div id="sessions">
"""
    
    for session in sessions_with_audio:
        try:
            file_size = session.audio_file.size if hasattr(session.audio_file, 'size') else 0
            html_content += f"""
            <div class="session">
                <h3>📚 {session.course.nom}</h3>
                <p><strong>👨‍🏫 Professeur:</strong> {session.professeur}</p>
                <p><strong>📅 Date:</strong> {session.date.strftime('%d/%m/%Y')}</p>
                <p><strong>📁 Fichier:</strong> {session.audio_file.name}</p>
                <p><strong>📏 Taille:</strong> {file_size} bytes</p>
                
                <div class="audio-player">
                    <audio controls preload="metadata" style="width: 100%;">
                        <source src="{session.audio_file.url}" type="audio/wav">
                        <source src="/api/courses/sessions/{session.id}/serve-audio/" type="audio/wav">
                        Votre navigateur ne supporte pas l'élément audio.
                    </audio>
                </div>
                
                <div class="test-results">
                    <button onclick="testAudioFile({session.id}, '{session.audio_file.url}')">
                        🧪 Tester ce fichier
                    </button>
                    <div id="result-{session.id}"></div>
                </div>
            </div>
            """
        except Exception as e:
            html_content += f"""
            <div class="session">
                <div class="error">Erreur session {session.id}: {e}</div>
            </div>
            """
    
    html_content += """
        </div>
        
        <div class="test-results">
            <h2>🧪 Tests Automatiques</h2>
            <button onclick="testAllAudioFiles()">Tester tous les fichiers</button>
            <div id="global-results"></div>
        </div>
    </div>

    <script>
        async function testAudioFile(sessionId, audioUrl) {
            const resultDiv = document.getElementById(`result-${sessionId}`);
            resultDiv.innerHTML = '<p>🔄 Test en cours...</p>';
            
            try {
                // Test 1: Vérifier l'URL directe
                const response = await fetch(audioUrl, { method: 'HEAD' });
                let results = `<div class="info">`;
                results += `<p><strong>Test URL directe:</strong> ${response.status} ${response.statusText}</p>`;
                
                if (response.ok) {
                    const contentLength = response.headers.get('content-length');
                    const contentType = response.headers.get('content-type');
                    results += `<p><strong>Taille:</strong> ${contentLength} bytes</p>`;
                    results += `<p><strong>Type:</strong> ${contentType}</p>`;
                }
                
                // Test 2: Vérifier l'API
                try {
                    const apiResponse = await fetch(`/api/courses/sessions/${sessionId}/audio-file/`);
                    const apiData = await apiResponse.json();
                    results += `<p><strong>Test API:</strong> ${apiResponse.status} ${apiResponse.statusText}</p>`;
                    if (apiData.success) {
                        results += `<p><strong>Fichier existe:</strong> ${apiData.file_info.exists ? 'Oui' : 'Non'}</p>`;
                    }
                } catch (apiError) {
                    results += `<p><strong>Test API:</strong> Erreur - ${apiError.message}</p>`;
                }
                
                results += `</div>`;
                
                if (response.ok) {
                    results = `<div class="success">${results}</div>`;
                } else {
                    results = `<div class="error">${results}</div>`;
                }
                
                resultDiv.innerHTML = results;
                
            } catch (error) {
                resultDiv.innerHTML = `<div class="error">❌ Erreur: ${error.message}</div>`;
            }
        }
        
        async function testAllAudioFiles() {
            const globalResults = document.getElementById('global-results');
            globalResults.innerHTML = '<p>🔄 Test de tous les fichiers en cours...</p>';
            
            const sessions = """ + str([s.id for s in sessions_with_audio]) + """;
            let allResults = '<div class="info"><h3>Résultats globaux:</h3>';
            
            for (const sessionId of sessions) {
                try {
                    const response = await fetch(`/api/courses/sessions/${sessionId}/audio-file/`);
                    const data = await response.json();
                    
                    if (data.success && data.file_info.exists) {
                        allResults += `<p>✅ Session ${sessionId}: OK</p>`;
                    } else {
                        allResults += `<p>❌ Session ${sessionId}: Fichier manquant</p>`;
                    }
                } catch (error) {
                    allResults += `<p>❌ Session ${sessionId}: Erreur - ${error.message}</p>`;
                }
            }
            
            allResults += '</div>';
            globalResults.innerHTML = allResults;
        }
        
        // Test automatique au chargement
        window.addEventListener('load', function() {
            console.log('🎵 Page de test audio chargée');
            console.log('Sessions disponibles:', """ + str([s.id for s in sessions_with_audio]) + """);
        });
    </script>
</body>
</html>
    """
    
    # Sauvegarder le fichier HTML
    html_file = BASE_DIR / "test_audio_web.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"  ✅ Page de test créée: {html_file}")
    print(f"  🌐 Ouvrez ce fichier dans votre navigateur pour tester")
    print(f"  📋 Ou copiez-le dans votre répertoire web pour un test complet")
    
    return str(html_file)

def main():
    """Fonction principale"""
    print("🎬 DÉMO COMPLÈTE AUDIO RESUME+")
    print("=" * 80)
    
    try:
        # 1. Créer des sessions avec de vrais fichiers audio
        sessions = create_demo_sessions_with_audio()
        
        if not sessions:
            print("❌ Impossible de créer les sessions de démonstration")
            return
        
        # 2. Créer des résumés IA
        create_demo_summaries()
        
        # 3. Tester les fichiers localement
        test_audio_files_locally()
        
        # 4. Créer une page de test HTML
        html_file = create_html_audio_test()
        
        print("\n" + "=" * 80)
        print("✅ DÉMO COMPLÈTE TERMINÉE")
        print("=" * 80)
        
        print(f"\n🎯 PROCHAINES ÉTAPES:")
        print(f"1. Ouvrez {html_file} dans votre navigateur")
        print(f"2. Testez la lecture audio directement")
        print(f"3. Vérifiez les endpoints API:")
        print(f"   - GET /api/courses/sessions/audio/")
        print(f"   - GET /api/courses/sessions/{{id}}/audio-file/")
        print(f"   - GET /api/courses/sessions/{{id}}/serve-audio/")
        
        print(f"\n📊 RÉSUMÉ:")
        print(f"   Sessions créées: {len(sessions)}")
        print(f"   Fichiers audio: {Session.objects.filter(audio_file__isnull=False).exclude(audio_file='').count()}")
        print(f"   Résumés IA: {Summary.objects.filter(author_type='ai').count()}")
        
    except Exception as e:
        print(f"❌ Erreur dans la démo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()