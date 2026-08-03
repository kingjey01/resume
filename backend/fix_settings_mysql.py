#!/usr/bin/env python3
"""
Script pour corriger les settings.py pour utiliser MySQL au lieu de SQLite3
"""

import os
import re

def fix_settings_mysql():
    settings_path = 'resume_backend/settings.py'
    
    if not os.path.exists(settings_path):
        print(f"❌ Fichier {settings_path} non trouvé")
        return False
    
    print(f"🔧 Correction de {settings_path} pour MySQL...")
    
    # Lire le fichier actuel
    with open(settings_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer la configuration SQLite par MySQL
    sqlite_pattern = r"DATABASES\s*=\s*\{[^}]*'ENGINE':\s*'django\.db\.backends\.sqlite3'[^}]*\}"
    
    mysql_config = """DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'resume_plus_db'),
        'USER': os.environ.get('DB_USER', 'resume_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'your_mysql_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}"""
    
    # Vérifier si la configuration MySQL existe déjà
    if 'django.db.backends.mysql' in content:
        print("✅ Configuration MySQL déjà présente")
        return True
    
    # Remplacer SQLite par MySQL
    if re.search(sqlite_pattern, content, re.DOTALL):
        content = re.sub(sqlite_pattern, mysql_config, content, flags=re.DOTALL)
        print("✓ Configuration SQLite remplacée par MySQL")
    else:
        print("⚠ Configuration SQLite non trouvée, ajout de la configuration MySQL")
        # Ajouter la configuration MySQL après les imports
        import_pattern = r"(from pathlib import Path.*?\n)"
        if re.search(import_pattern, content, re.DOTALL):
            content = re.sub(import_pattern, r"\1\nimport os\n", content, flags=re.DOTALL)
        
        # Ajouter la configuration à la fin
        content += f"\n\n# Database Configuration\n{mysql_config}\n"
    
    # Ajouter l'import os si nécessaire
    if 'import os' not in content:
        content = 'import os\n' + content
    
    # Sauvegarder le fichier modifié
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fichier settings.py mis à jour avec succès")
    return True

def create_env_file():
    """Créer un fichier .env avec les variables MySQL"""
    env_content = """# Configuration MySQL pour Resume+
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this-in-production

# Base de données MySQL
DB_NAME=resume_plus_db
DB_USER=resume_user
DB_PASSWORD=your_mysql_password_here
DB_HOST=localhost
DB_PORT=3306

# Domaines autorisés
ALLOWED_HOSTS=resumecours.gestionhospitaliare.site,www.resumecours.gestionhospitaliare.site,localhost,127.0.0.1
"""
    
    env_path = '.env'
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"✅ Fichier {env_path} créé")
        print("⚠ N'oubliez pas de modifier DB_PASSWORD avec votre vrai mot de passe MySQL")
    else:
        print(f"ℹ Fichier {env_path} existe déjà")

if __name__ == '__main__':
    print("🔧 Correction des settings pour MySQL")
    print("=" * 40)
    
    success = fix_settings_mysql()
    if success:
        create_env_file()
        print("\n✅ Configuration terminée!")
        print("\n📝 Prochaines étapes:")
        print("1. Modifiez le fichier .env avec vos vraies informations MySQL")
        print("2. Installez python-decouple: pip install python-decouple")
        print("3. Exécutez: python create_test_data_mysql.py")
    else:
        print("\n❌ Erreur lors de la configuration")