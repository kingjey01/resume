#!/usr/bin/env python3
"""
Debug des modules manquants
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def test_imports():
    """Test des imports nécessaires pour l'upload audio"""
    print("🔍 Test des imports Python...")
    
    modules_to_test = [
        ('wave', 'Module wave (audio WAV)'),
        ('io', 'Module io (fichiers en mémoire)'),
        ('struct', 'Module struct (données binaires)'),
        ('django.core.files', 'Django files'),
        ('rest_framework', 'Django REST Framework'),
        ('courses.models', 'Models courses'),
        ('courses.serializers', 'Serializers courses'),
        ('courses.audio_processing', 'Audio processing (optionnel)'),
    ]
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {description}")
        except ImportError as e:
            print(f"❌ {description}: {e}")
        except Exception as e:
            print(f"⚠️  {description}: {e}")

def test_audio_processing_import():
    """Test spécifique du module audio_processing"""
    print(f"\n🎵 Test du module audio_processing...")
    
    try:
        from courses.audio_processing import audio_processor
        print("✅ audio_processor importé avec succès")
        
        # Tester les méthodes
        if hasattr(audio_processor, 'process_audio_session'):
            print("✅ Méthode process_audio_session disponible")
        else:
            print("❌ Méthode process_audio_session manquante")
            
    except ImportError as e:
        print(f"❌ Impossible d'importer audio_processor: {e}")
    except Exception as e:
        print(f"⚠️  Erreur audio_processor: {e}")

def test_view_import():
    """Test de l'import de la vue upload_audio_session"""
    print(f"\n📤 Test de l'import de la vue upload...")
    
    try:
        from courses.views import upload_audio_session
        print("✅ Vue upload_audio_session importée")
        
        # Vérifier les décorateurs
        print(f"📋 Décorateurs: {getattr(upload_audio_session, '__wrapped__', 'Aucun')}")
        
    except ImportError as e:
        print(f"❌ Impossible d'importer upload_audio_session: {e}")
    except Exception as e:
        print(f"⚠️  Erreur upload_audio_session: {e}")

def check_python_path():
    """Vérifier le PYTHON_PATH"""
    print(f"\n🐍 Vérification du Python Path...")
    
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Django version: {django.get_version()}")
    
    print(f"\nPython Path:")
    for i, path in enumerate(sys.path):
        print(f"  {i+1}. {path}")

def main():
    print("🚀 DIAGNOSTIC DES MODULES PYTHON")
    print("="*50)
    
    test_imports()
    test_audio_processing_import()
    test_view_import()
    check_python_path()
    
    print(f"\n{'='*50}")
    print("📋 ACTIONS RECOMMANDÉES")
    print('='*50)
    print("1. Vérifiez les logs Apache pour voir le module exact manquant")
    print("2. Installez les modules manquants avec pip")
    print("3. Redémarrez Apache après installation")

if __name__ == "__main__":
    main()