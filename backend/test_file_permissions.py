#!/usr/bin/env python3
"""
Test des permissions de fichiers
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

def test_media_permissions():
    """Test des permissions du dossier media"""
    print("🔍 Test des permissions du dossier media...")
    
    media_root = settings.MEDIA_ROOT
    audio_dir = os.path.join(media_root, 'audio_sessions')
    
    print(f"📁 MEDIA_ROOT: {media_root}")
    print(f"📁 Audio dir: {audio_dir}")
    
    # Vérifier l'existence des dossiers
    if os.path.exists(media_root):
        print(f"✅ MEDIA_ROOT existe")
        print(f"   Permissions: {oct(os.stat(media_root).st_mode)[-3:]}")
    else:
        print(f"❌ MEDIA_ROOT n'existe pas")
        return False
    
    if os.path.exists(audio_dir):
        print(f"✅ audio_sessions/ existe")
        print(f"   Permissions: {oct(os.stat(audio_dir).st_mode)[-3:]}")
    else:
        print(f"❌ audio_sessions/ n'existe pas")
        try:
            os.makedirs(audio_dir, exist_ok=True)
            print(f"✅ audio_sessions/ créé")
        except Exception as e:
            print(f"❌ Impossible de créer audio_sessions/: {e}")
            return False
    
    # Test d'écriture
    test_file_path = os.path.join(audio_dir, 'test_permissions.txt')
    try:
        with open(test_file_path, 'w') as f:
            f.write("Test de permissions")
        print(f"✅ Écriture de fichier réussie")
        
        # Nettoyer
        os.remove(test_file_path)
        print(f"✅ Suppression de fichier réussie")
        return True
        
    except Exception as e:
        print(f"❌ Erreur d'écriture: {e}")
        return False

def test_django_file_upload():
    """Test d'upload de fichier via Django"""
    print(f"\n📤 Test d'upload via Django...")
    
    try:
        # Créer un fichier de test
        test_content = b"Test audio file content"
        test_file = ContentFile(test_content, name='test_audio.wav')
        
        # Sauvegarder via Django storage
        file_path = default_storage.save('audio_sessions/test_upload.wav', test_file)
        print(f"✅ Upload Django réussi: {file_path}")
        
        # Vérifier l'existence
        if default_storage.exists(file_path):
            print(f"✅ Fichier existe dans le storage")
            
            # Nettoyer
            default_storage.delete(file_path)
            print(f"✅ Fichier supprimé")
            return True
        else:
            print(f"❌ Fichier non trouvé dans le storage")
            return False
            
    except Exception as e:
        print(f"❌ Erreur upload Django: {e}")
        return False

def check_wsgi_user():
    """Vérifier l'utilisateur WSGI"""
    print(f"\n👤 Vérification de l'utilisateur WSGI...")
    
    import pwd
    import os
    
    current_uid = os.getuid()
    current_user = pwd.getpwuid(current_uid).pw_name
    
    print(f"🆔 UID actuel: {current_uid}")
    print(f"👤 Utilisateur actuel: {current_user}")
    
    # Vérifier les permissions sur MEDIA_ROOT
    media_root = settings.MEDIA_ROOT
    if os.path.exists(media_root):
        stat_info = os.stat(media_root)
        owner_uid = stat_info.st_uid
        owner_user = pwd.getpwuid(owner_uid).pw_name
        
        print(f"📁 Propriétaire de MEDIA_ROOT: {owner_user} (UID: {owner_uid})")
        
        if current_uid == owner_uid:
            print(f"✅ L'utilisateur WSGI est propriétaire du dossier media")
            return True
        else:
            print(f"❌ L'utilisateur WSGI n'est PAS propriétaire du dossier media")
            return False
    
    return False

def main():
    print("🚀 TEST DES PERMISSIONS DE FICHIERS")
    print("="*50)
    
    # Tests
    media_ok = test_media_permissions()
    django_ok = test_django_file_upload()
    user_ok = check_wsgi_user()
    
    print(f"\n{'='*50}")
    print("📋 RÉSUMÉ")
    print('='*50)
    print(f"Permissions media: {'✅' if media_ok else '❌'}")
    print(f"Upload Django: {'✅' if django_ok else '❌'}")
    print(f"Utilisateur WSGI: {'✅' if user_ok else '❌'}")
    
    if media_ok and django_ok:
        print("✅ Les permissions sont correctes!")
        print("✅ L'upload audio devrait maintenant fonctionner!")
    else:
        print("❌ Des problèmes de permissions persistent")
        print("❌ Vérifiez les permissions avec les commandes suggérées")

if __name__ == "__main__":
    main()