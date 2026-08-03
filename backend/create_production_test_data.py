#!/usr/bin/env python3
"""
Créer des données de test directement sur le serveur de production
"""

import os
import sys
import django
from pathlib import Path
import wave
import struct
import math

# Configuration Django pour la production
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
from django.utils import timezone

def create_production_audio_files():
    """Créer des fichiers audio de production avec de vrais sons"""
    print("🎵 CRÉATION DE FICHIERS AUDIO POUR LA PRODUCTION")
    print("=" * 60)
    
    # Vérifier qu'on a des cours
    courses = Course.objects.all()
    if not courses.exists():
        print("❌ Aucun cours trouvé. Exécutez d'abord create_test_data.py")
        return False
    
    print(f"📚 Cours disponibles: {courses.count()}")
    
    # Créer le répertoire media s'il n'existe pas
    media_dir = BASE_DIR / "media" / "audio_sessions"
    media_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Répertoire media: {media_dir}")
    
    # Définir les sessions de démonstration avec des sons différents
    demo_sessions = [
        {
            'course': courses[0],
            'professeur': 'Prof. Martin Dubois',
            'duration': 12,
            'frequencies': [440, 523, 659],  # Accord majeur (La, Do, Mi)
            'title': 'Introduction Variables et Types',
            'description': 'Cours sur les variables et types de données en programmation'
        },
        {
            'course': courses[1] if len(courses) > 1 else courses[0],
            'professeur': 'Prof. Sarah Johnson',
            'duration': 8,
            'frequencies': [349, 415, 523],  # Accord Fa majeur
            'title': 'Structures de Contrôle',
            'description': 'Les boucles et conditions en programmation'
        },
        {
            'course': courses[2] if len(courses) > 2 else courses[0],
            'professeur': 'Prof. Ahmed Hassan',
            'duration': 15,
            'frequencies': [294, 349, 440],  # Accord Ré mineur
            'title': 'Bases de Données Relationnelles',
            'description': 'Introduction aux SGBD et SQL'
        },
        {
            'course': courses[0],
            'professeur': 'Prof. Lisa Chen',
            'duration': 10,
            'frequencies': [523, 659, 784],  # Accord Do majeur aigu
            'title': 'Algorithmes de Tri',
            'description': 'Étude des algorithmes de tri classiques'
        },
        {
            'course': courses[1] if len(courses) > 1 else courses[0],
            'professeur': 'Prof. Jean Dupont',
            'duration': 6,
            'frequencies': [220, 277, 330],  # Accord La mineur grave
            'title': 'Fonctions et Procédures',
            'description': 'Programmation modulaire et fonctions'
        }
    ]
    
    created_sessions = []
    
    for i, session_data in enumerate(demo_sessions):
        try:
            print(f"\n🎬 Création session {i+1}: {session_data['title']}")
            
            # Créer la session
            session = Session.objects.create(
                course=session_data['course'],
                date=timezone.now() - timezone.timedelta(days=i+1, hours=i*2),
                professeur=session_data['professeur']
            )
            
            # Créer un fichier audio avec mélodie
            filename = f'prod_session_{session.id}_{session_data["title"].lower().replace(" ", "_")}.wav'
            audio_content = create_melodic_wav_file(
                filename,
                session_data['duration'],
                session_data['frequencies']
            )
            
            # Sauvegarder le fichier
            session.audio_file.save(
                filename,
                ContentFile(audio_content),
                save=True
            )
            
            created_sessions.append(session)
            
            print(f"   ✅ Session {session.id} créée")
            print(f"   📁 Fichier: {session.audio_file.name}")
            print(f"   🎵 Durée: {session_data['duration']}s")
            print(f"   📏 Taille: {len(audio_content)} bytes ({len(audio_content)//1024}KB)")
            
            # Créer un résumé IA automatiquement
            create_ai_summary_for_session(session, session_data)
            
        except Exception as e:
            print(f"   ❌ Erreur session {i+1}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎯 RÉSUMÉ:")
    print(f"   Sessions créées: {len(created_sessions)}")
    print(f"   Fichiers audio: {len(created_sessions)}")
    
    return created_sessions

def create_melodic_wav_file(filename, duration, frequencies):
    """Créer un fichier WAV avec une mélodie"""
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    
    print(f"   🎵 Génération audio: {filename}")
    print(f"      Durée: {duration}s, Fréquences: {frequencies}")
    
    samples = []
    
    for i in range(num_samples):
        t = i / sample_rate
        
        # Fade in/out pour éviter les clics
        fade_duration = 0.2
        if t < fade_duration:
            fade = t / fade_duration
        elif t > duration - fade_duration:
            fade = (duration - t) / fade_duration
        else:
            fade = 1.0
        
        # Créer une mélodie qui change de fréquence
        segment_duration = duration / len(frequencies)
        current_freq_index = min(int(t / segment_duration), len(frequencies) - 1)
        current_freq = frequencies[current_freq_index]
        
        # Transition douce entre les fréquences
        if current_freq_index < len(frequencies) - 1:
            next_freq = frequencies[current_freq_index + 1]
            segment_progress = (t % segment_duration) / segment_duration
            
            # Transition dans les derniers 20% du segment
            if segment_progress > 0.8:
                transition_progress = (segment_progress - 0.8) / 0.2
                current_freq = current_freq * (1 - transition_progress) + next_freq * transition_progress
        
        # Générer l'onde avec harmoniques
        amplitude = 0.3 * fade
        sample_value = (
            amplitude * math.sin(2 * math.pi * current_freq * t) +
            amplitude * 0.3 * math.sin(2 * math.pi * current_freq * 2 * t) +
            amplitude * 0.1 * math.sin(2 * math.pi * current_freq * 3 * t) +
            amplitude * 0.05 * math.sin(2 * math.pi * current_freq * 0.5 * t)  # Sub-harmonique
        )
        
        # Ajouter un peu de "respiration" (variation d'amplitude)
        breath = 1 + 0.1 * math.sin(2 * math.pi * 0.5 * t)  # Variation lente
        sample_value *= breath
        
        # Convertir en entier 16-bit
        sample_int = int(sample_value * 32767)
        sample_int = max(-32768, min(32767, sample_int))
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
    
    return wav_buffer.getvalue()

def create_ai_summary_for_session(session, session_data):
    """Créer un résumé IA pour une session"""
    try:
        # Vérifier si un résumé existe déjà
        existing_summary = Summary.objects.filter(session=session, author_type='ai').first()
        if existing_summary:
            print(f"   ℹ️ Résumé IA existe déjà")
            return existing_summary
        
        # Créer le contenu du résumé
        summary_text = f"""
🎓 RÉSUMÉ AUTOMATIQUE - {session.course.nom}
👨‍🏫 Professeur: {session.professeur}
📅 Date: {session.date.strftime('%d/%m/%Y à %H:%M')}
⏱️ Durée: {session_data['duration']} minutes

📋 DESCRIPTION DU COURS:
{session_data['description']}

🔑 POINTS CLÉS ABORDÉS:
• Introduction aux concepts fondamentaux
• Définitions et terminologie importante
• Exemples pratiques et cas d'usage
• Exercices d'application
• Questions-réponses avec les étudiants

💡 CONTENU DÉTAILLÉ:
Le professeur {session.professeur} a présenté de manière structurée les éléments 
essentiels de {session.course.nom}. La séance était interactive avec de nombreux 
exemples concrets pour faciliter la compréhension des étudiants.

Les concepts abordés incluent les bases théoriques ainsi que leur application 
pratique dans des contextes réels. Des exercices ont été proposés pour 
consolider les acquis.

🎯 OBJECTIFS PÉDAGOGIQUES ATTEINTS:
• Compréhension des concepts de base
• Maîtrise de la terminologie spécialisée  
• Capacité d'application pratique
• Développement de l'esprit critique

📚 RESSOURCES COMPLÉMENTAIRES:
• Documentation technique disponible
• Exercices pratiques à réaliser
• Lectures recommandées pour approfondir

🎵 INFORMATIONS TECHNIQUES:
• Enregistrement audio de qualité professionnelle
• Durée: {session_data['duration']} minutes
• Format: WAV haute définition
• Transcription automatique disponible

⚡ GÉNÉRÉ AUTOMATIQUEMENT PAR IA
Ce résumé a été créé par intelligence artificielle à partir de l'analyse 
de l'enregistrement audio de la séance. Pour plus de détails, consultez 
l'enregistrement complet ou contactez le professeur.

🔄 Dernière mise à jour: {session.date.strftime('%d/%m/%Y à %H:%M')}
        """.strip()
        
        # Créer le résumé
        summary = Summary.objects.create(
            titre=f"Résumé IA - {session_data['title']} ({session.date.strftime('%d/%m')})",
            texte_resume=summary_text,
            course=session.course,
            session=session,
            author_type='ai',
            prix=0.00,
            is_free=True
        )
        
        print(f"   ✅ Résumé IA créé (ID: {summary.id})")
        return summary
        
    except Exception as e:
        print(f"   ❌ Erreur création résumé: {e}")
        return None

def verify_production_setup():
    """Vérifier la configuration de production"""
    print("\n🔍 VÉRIFICATION DE LA CONFIGURATION PRODUCTION")
    print("=" * 60)
    
    try:
        from django.conf import settings
        
        print(f"📁 BASE_DIR: {settings.BASE_DIR}")
        print(f"📁 MEDIA_ROOT: {getattr(settings, 'MEDIA_ROOT', 'Non défini')}")
        print(f"🔗 MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'Non défini')}")
        print(f"🔧 DEBUG: {settings.DEBUG}")
        
        # Vérifier la base de données
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print(f"✅ Connexion base de données OK")
        
        # Vérifier les modèles
        courses_count = Course.objects.count()
        sessions_count = Session.objects.count()
        summaries_count = Summary.objects.count()
        
        print(f"📊 Cours: {courses_count}")
        print(f"📊 Sessions: {sessions_count}")
        print(f"📊 Résumés: {summaries_count}")
        
        # Vérifier les répertoires
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if media_root:
            media_path = Path(media_root)
            audio_path = media_path / "audio_sessions"
            
            print(f"📁 Répertoire media existe: {media_path.exists()}")
            print(f"📁 Répertoire audio existe: {audio_path.exists()}")
            
            if audio_path.exists():
                audio_files = list(audio_path.glob("*.wav"))
                print(f"🎵 Fichiers audio existants: {len(audio_files)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        return False

def create_production_test_page():
    """Créer une page de test pour la production"""
    print("\n🌐 CRÉATION DE LA PAGE DE TEST PRODUCTION")
    print("=" * 60)
    
    try:
        sessions_with_audio = Session.objects.filter(
            audio_file__isnull=False
        ).exclude(audio_file='').order_by('-created_at')
        
        html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Audio Resume+ - Production</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #333; margin: 0; font-size: 2.5em; }}
        .header p {{ color: #666; font-size: 1.1em; margin: 10px 0; }}
        .session {{ margin: 25px 0; padding: 20px; border: 2px solid #e0e0e0; border-radius: 10px; background: #f9f9f9; }}
        .session:hover {{ border-color: #667eea; background: #f0f4ff; }}
        .session h3 {{ margin-top: 0; color: #333; font-size: 1.4em; }}
        .session-info {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; }}
        .info-item {{ background: white; padding: 10px; border-radius: 5px; border-left: 4px solid #667eea; }}
        .audio-player {{ margin: 20px 0; }}
        .audio-player audio {{ width: 100%; height: 40px; }}
        .test-buttons {{ margin: 15px 0; }}
        .test-buttons button {{ background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; font-size: 14px; }}
        .test-buttons button:hover {{ background: #5a67d8; }}
        .test-buttons button.secondary {{ background: #48bb78; }}
        .test-buttons button.danger {{ background: #f56565; }}
        .results {{ margin: 15px 0; padding: 15px; border-radius: 5px; }}
        .success {{ background: #c6f6d5; border: 1px solid #48bb78; color: #22543d; }}
        .error {{ background: #fed7d7; border: 1px solid #f56565; color: #742a2a; }}
        .info {{ background: #bee3f8; border: 1px solid #3182ce; color: #2a4365; }}
        .warning {{ background: #faf089; border: 1px solid #d69e2e; color: #744210; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; }}
        .stat-label {{ font-size: 0.9em; opacity: 0.9; }}
        .global-tests {{ margin: 30px 0; padding: 20px; background: #f7fafc; border-radius: 10px; }}
        .loading {{ display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 Test Audio Resume+ - Production</h1>
            <p>Serveur: <strong>resumecours.gestionhospitaliare.site</strong></p>
            <p>Date: <strong>{timezone.now().strftime('%d/%m/%Y à %H:%M')}</strong></p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{sessions_with_audio.count()}</div>
                <div class="stat-label">Sessions Audio</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{Course.objects.count()}</div>
                <div class="stat-label">Cours</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{Summary.objects.filter(author_type='ai').count()}</div>
                <div class="stat-label">Résumés IA</div>
            </div>
        </div>
        
        <div class="global-tests">
            <h2>🧪 Tests Globaux</h2>
            <div class="test-buttons">
                <button onclick="testAllEndpoints()">Tester tous les endpoints</button>
                <button onclick="testAllAudioFiles()" class="secondary">Tester tous les fichiers audio</button>
                <button onclick="testApiConnectivity()" class="danger">Test connectivité API</button>
            </div>
            <div id="global-results"></div>
        </div>
        
        <h2>🎵 Sessions Audio Disponibles</h2>
        <div id="sessions">
"""
        
        for session in sessions_with_audio:
            try:
                file_size = session.audio_file.size if hasattr(session.audio_file, 'size') else 0
                file_size_mb = round(file_size / (1024 * 1024), 2) if file_size else 0
                
                html_content += f"""
            <div class="session">
                <h3>📚 {session.course.nom}</h3>
                
                <div class="session-info">
                    <div class="info-item">
                        <strong>👨‍🏫 Professeur:</strong><br>{session.professeur}
                    </div>
                    <div class="info-item">
                        <strong>📅 Date:</strong><br>{session.date.strftime('%d/%m/%Y à %H:%M')}
                    </div>
                    <div class="info-item">
                        <strong>📁 Fichier:</strong><br>{session.audio_file.name}
                    </div>
                    <div class="info-item">
                        <strong>📏 Taille:</strong><br>{file_size_mb} MB ({file_size} bytes)
                    </div>
                </div>
                
                <div class="audio-player">
                    <audio controls preload="metadata">
                        <source src="{session.audio_file.url}" type="audio/wav">
                        <source src="/api/courses/sessions/{session.id}/serve-audio/" type="audio/wav">
                        Votre navigateur ne supporte pas l'élément audio.
                    </audio>
                </div>
                
                <div class="test-buttons">
                    <button onclick="testSessionAudio({session.id})">🧪 Tester cette session</button>
                    <button onclick="testDirectAccess('{session.audio_file.url}')" class="secondary">🔗 Test accès direct</button>
                    <button onclick="testApiEndpoint({session.id})" class="danger">📡 Test API</button>
                </div>
                
                <div id="result-{session.id}"></div>
            </div>
                """
            except Exception as e:
                html_content += f"""
            <div class="session">
                <div class="error">❌ Erreur session {session.id}: {e}</div>
            </div>
                """
        
        html_content += f"""
        </div>
    </div>

    <script>
        const BASE_URL = 'https://resumecours.gestionhospitaliare.site/api/courses';
        
        function showLoading(elementId) {{
            document.getElementById(elementId).innerHTML = '<div class="info"><span class="loading"></span> Test en cours...</div>';
        }}
        
        function showResult(elementId, content, type = 'info') {{
            document.getElementById(elementId).innerHTML = `<div class="${{type}}">${{content}}</div>`;
        }}
        
        async function testSessionAudio(sessionId) {{
            const resultId = `result-${{sessionId}}`;
            showLoading(resultId);
            
            let results = '<h4>Résultats des tests:</h4>';
            
            try {{
                // Test 1: API audio-file
                const apiResponse = await fetch(`${{BASE_URL}}/sessions/${{sessionId}}/audio-file/`);
                results += `<p><strong>📡 API audio-file:</strong> ${{apiResponse.status}} ${{apiResponse.statusText}}</p>`;
                
                if (apiResponse.ok) {{
                    const apiData = await apiResponse.json();
                    if (apiData.success) {{
                        results += `<p>✅ Fichier trouvé: ${{apiData.file_info.name}}</p>`;
                        results += `<p>📏 Taille: ${{apiData.file_info.size_mb}} MB</p>`;
                        results += `<p>🔗 URL: <a href="${{apiData.audio_url}}" target="_blank">Ouvrir</a></p>`;
                        
                        // Test 2: Accès direct au fichier
                        try {{
                            const directResponse = await fetch(apiData.audio_url, {{ method: 'HEAD' }});
                            results += `<p><strong>🌐 Accès direct:</strong> ${{directResponse.status}} ${{directResponse.statusText}}</p>`;
                            
                            if (directResponse.ok) {{
                                const contentType = directResponse.headers.get('content-type');
                                const contentLength = directResponse.headers.get('content-length');
                                results += `<p>🎵 Type: ${{contentType}}</p>`;
                                results += `<p>📏 Taille header: ${{contentLength}} bytes</p>`;
                            }}
                        }} catch (directError) {{
                            results += `<p>❌ Erreur accès direct: ${{directError.message}}</p>`;
                        }}
                    }} else {{
                        results += `<p>❌ Erreur API: ${{apiData.error}}</p>`;
                    }}
                }}
                
                // Test 3: Endpoint serve-audio
                try {{
                    const serveResponse = await fetch(`${{BASE_URL}}/sessions/${{sessionId}}/serve-audio/`, {{ method: 'HEAD' }});
                    results += `<p><strong>🎵 Serve-audio:</strong> ${{serveResponse.status}} ${{serveResponse.statusText}}</p>`;
                    
                    if (serveResponse.ok) {{
                        const contentType = serveResponse.headers.get('content-type');
                        const acceptRanges = serveResponse.headers.get('accept-ranges');
                        results += `<p>✅ Streaming OK - Type: ${{contentType}}, Ranges: ${{acceptRanges}}</p>`;
                    }}
                }} catch (serveError) {{
                    results += `<p>❌ Erreur serve-audio: ${{serveError.message}}</p>`;
                }}
                
                showResult(resultId, results, 'success');
                
            }} catch (error) {{
                showResult(resultId, `❌ Erreur générale: ${{error.message}}`, 'error');
            }}
        }}
        
        async function testDirectAccess(audioUrl) {{
            try {{
                const response = await fetch(audioUrl, {{ method: 'HEAD' }});
                alert(`Accès direct: ${{response.status}} ${{response.statusText}}\\nType: ${{response.headers.get('content-type')}}`);
            }} catch (error) {{
                alert(`Erreur accès direct: ${{error.message}}`);
            }}
        }}
        
        async function testApiEndpoint(sessionId) {{
            try {{
                const response = await fetch(`${{BASE_URL}}/sessions/${{sessionId}}/audio-file/`);
                const data = await response.json();
                
                if (data.success) {{
                    alert(`✅ API OK\\nFichier: ${{data.file_info.name}}\\nTaille: ${{data.file_info.size_mb}} MB`);
                }} else {{
                    alert(`❌ Erreur API: ${{data.error}}`);
                }}
            }} catch (error) {{
                alert(`❌ Erreur: ${{error.message}}`);
            }}
        }}
        
        async function testAllEndpoints() {{
            showLoading('global-results');
            
            const endpoints = [
                '/courses/',
                '/sessions/',
                '/sessions/audio/',
                '/sessions/audio/stats/',
                '/summaries/'
            ];
            
            let results = '<h4>Test de tous les endpoints:</h4>';
            
            for (const endpoint of endpoints) {{
                try {{
                    const response = await fetch(BASE_URL + endpoint);
                    const status = response.ok ? '✅' : '❌';
                    results += `<p>${{status}} ${{endpoint}}: ${{response.status}} ${{response.statusText}}</p>`;
                }} catch (error) {{
                    results += `<p>❌ ${{endpoint}}: ${{error.message}}</p>`;
                }}
            }}
            
            showResult('global-results', results, 'info');
        }}
        
        async function testAllAudioFiles() {{
            showLoading('global-results');
            
            try {{
                const response = await fetch(`${{BASE_URL}}/sessions/audio/`);
                
                if (response.ok) {{
                    const data = await response.json();
                    const sessions = data.sessions || [];
                    
                    let results = `<h4>Test de ${{sessions.length}} fichiers audio:</h4>`;
                    
                    for (const session of sessions.slice(0, 5)) {{
                        try {{
                            const audioResponse = await fetch(`${{BASE_URL}}/sessions/${{session.id}}/audio-file/`);
                            const audioData = await audioResponse.json();
                            
                            if (audioData.success && audioData.file_info.exists) {{
                                results += `<p>✅ Session ${{session.id}}: OK (${{audioData.file_info.size_mb}} MB)</p>`;
                            }} else {{
                                results += `<p>❌ Session ${{session.id}}: Fichier manquant</p>`;
                            }}
                        }} catch (error) {{
                            results += `<p>❌ Session ${{session.id}}: ${{error.message}}</p>`;
                        }}
                    }}
                    
                    showResult('global-results', results, 'success');
                }} else {{
                    showResult('global-results', `❌ Erreur récupération sessions: ${{response.status}}`, 'error');
                }}
            }} catch (error) {{
                showResult('global-results', `❌ Erreur: ${{error.message}}`, 'error');
            }}
        }}
        
        async function testApiConnectivity() {{
            showLoading('global-results');
            
            try {{
                const start = Date.now();
                const response = await fetch(`${{BASE_URL}}/courses/`);
                const duration = Date.now() - start;
                
                let results = `<h4>Test de connectivité API:</h4>`;
                results += `<p>🌐 Serveur: resumecours.gestionhospitaliare.site</p>`;
                results += `<p>⏱️ Temps de réponse: ${{duration}}ms</p>`;
                results += `<p>📊 Status: ${{response.status}} ${{response.statusText}}</p>`;
                
                if (response.ok) {{
                    results += `<p>✅ Connectivité OK</p>`;
                    showResult('global-results', results, 'success');
                }} else {{
                    results += `<p>❌ Problème de connectivité</p>`;
                    showResult('global-results', results, 'warning');
                }}
            }} catch (error) {{
                showResult('global-results', `❌ Erreur de connectivité: ${{error.message}}`, 'error');
            }}
        }}
        
        // Test automatique au chargement
        window.addEventListener('load', function() {{
            console.log('🎵 Page de test production chargée');
            console.log('Serveur:', BASE_URL);
            
            // Test de connectivité automatique
            setTimeout(testApiConnectivity, 1000);
        }});
    </script>
</body>
</html>
        """
        
        # Sauvegarder le fichier HTML
        html_file = BASE_DIR / "test_production_audio.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"   ✅ Page de test production créée: {html_file}")
        print(f"   🌐 Copiez ce fichier sur votre serveur web pour un test complet")
        
        return str(html_file)
        
    except Exception as e:
        print(f"   ❌ Erreur création page: {e}")
        return None

def main():
    """Fonction principale"""
    print("🚀 CRÉATION DE DONNÉES DE TEST POUR LA PRODUCTION")
    print("=" * 80)
    
    try:
        # 1. Vérifier la configuration
        if not verify_production_setup():
            print("❌ Configuration incorrecte, arrêt du script")
            return
        
        # 2. Créer les fichiers audio
        sessions = create_production_audio_files()
        
        if not sessions:
            print("❌ Aucune session créée")
            return
        
        # 3. Créer la page de test
        html_file = create_production_test_page()
        
        print("\n" + "=" * 80)
        print("✅ CRÉATION TERMINÉE AVEC SUCCÈS")
        print("=" * 80)
        
        print(f"\n🎯 RÉSUMÉ:")
        print(f"   Sessions créées: {len(sessions)}")
        print(f"   Fichiers audio: {len(sessions)}")
        print(f"   Résumés IA: {Summary.objects.filter(author_type='ai').count()}")
        
        if html_file:
            print(f"   Page de test: {html_file}")
        
        print(f"\n📋 PROCHAINES ÉTAPES:")
        print(f"1. Testez avec: python test_production_audio.py")
        print(f"2. Ouvrez la page HTML dans votre navigateur")
        print(f"3. Vérifiez que les fichiers sont accessibles via HTTPS")
        print(f"4. Testez l'intégration avec l'application Flutter")
        
        print(f"\n🔗 URLs de test:")
        print(f"   API: https://resumecours.gestionhospitaliare.site/api/courses/sessions/audio/")
        print(f"   Media: https://resumecours.gestionhospitaliare.site/media/audio_sessions/")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()