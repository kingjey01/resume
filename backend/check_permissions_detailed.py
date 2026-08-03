#!/usr/bin/env python3
"""
Vérification détaillée des permissions
"""
import os
import sys
import django
import pwd
import grp
import stat

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings

def check_file_permissions(path):
    """Vérifier les permissions d'un fichier/dossier"""
    if not os.path.exists(path):
        return f"❌ N'existe pas: {path}"
    
    stat_info = os.stat(path)
    
    # Permissions en octal
    perms = oct(stat_info.st_mode)[-3:]
    
    # Propriétaire et groupe
    try:
        owner = pwd.getpwuid(stat_info.st_uid).pw_name
    except KeyError:
        owner = f"UID:{stat_info.st_uid}"
    
    try:
        group = grp.getgrgid(stat_info.st_gid).gr_name
    except KeyError:
        group = f"GID:{stat_info.st_gid}"
    
    # Type
    if os.path.isdir(path):
        file_type = "📁 Dossier"
    else:
        file_type = "📄 Fichier"
    
    return f"✅ {file_type} {perms} {owner}:{group} {path}"

def check_write_permission(path):
    """Tester l'écriture dans un dossier"""
    test_file = os.path.join(path, 'test_write_permission.tmp')
    
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        return f"✅ Écriture OK dans {path}"
    except Exception as e:
        return f"❌ Écriture ÉCHOUE dans {path}: {e}"

def get_current_user_info():
    """Informations sur l'utilisateur actuel"""
    uid = os.getuid()
    gid = os.getgid()
    
    try:
        username = pwd.getpwuid(uid).pw_name
    except KeyError:
        username = f"UID:{uid}"
    
    try:
        groupname = grp.getgrgid(gid).gr_name
    except KeyError:
        groupname = f"GID:{gid}"
    
    return uid, gid, username, groupname

def main():
    print("🔍 VÉRIFICATION DÉTAILLÉE DES PERMISSIONS")
    print("="*60)
    
    # Informations utilisateur actuel
    uid, gid, username, groupname = get_current_user_info()
    print(f"👤 Utilisateur actuel: {username} (UID:{uid})")
    print(f"👥 Groupe actuel: {groupname} (GID:{gid})")
    
    # Chemins à vérifier
    media_root = settings.MEDIA_ROOT
    audio_dir = os.path.join(media_root, 'audio_sessions')
    summaries_dir = os.path.join(media_root, 'summaries')
    
    print(f"\n📁 VÉRIFICATION DES DOSSIERS:")
    print("-" * 60)
    
    paths_to_check = [
        media_root,
        audio_dir,
        summaries_dir,
    ]
    
    for path in paths_to_check:
        print(check_file_permissions(path))
    
    print(f"\n✍️  TEST D'ÉCRITURE:")
    print("-" * 60)
    
    # Test d'écriture
    if os.path.exists(audio_dir):
        print(check_write_permission(audio_dir))
    else:
        print(f"❌ Dossier audio_sessions n'existe pas")
    
    if os.path.exists(summaries_dir):
        print(check_write_permission(summaries_dir))
    else:
        print(f"❌ Dossier summaries n'existe pas")
    
    # Recommandations
    print(f"\n🔧 COMMANDES DE CORRECTION:")
    print("-" * 60)
    print(f"# Pour corriger les permissions:")
    print(f"sudo chown -R jey:jey {media_root}")
    print(f"sudo chmod -R 775 {media_root}")
    print(f"sudo chmod 777 {audio_dir}")
    print(f"")
    print(f"# Pour Apache/WSGI:")
    print(f"sudo chgrp -R apache {media_root} 2>/dev/null || sudo chgrp -R www-data {media_root}")
    print(f"sudo systemctl restart httpd")

if __name__ == "__main__":
    main()