#!/usr/bin/env python3
"""
Créer la table authtoken_token manuellement
"""

import pymysql
import secrets
import string
from datetime import datetime

def create_token_table():
    """Créer la table authtoken_token si elle n'existe pas"""
    print("🔧 CRÉATION DE LA TABLE AUTHTOKEN_TOKEN")
    print("=" * 60)
    
    try:
        connection = pymysql.connect(
            host='localhost',
            user='jey_resume',
            password='1234',
            database='jey_resume',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Vérifier si la table existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'jey_resume' 
            AND table_name = 'authtoken_token'
        """)
        
        table_exists = cursor.fetchone()[0] > 0
        
        if table_exists:
            print("✅ Table authtoken_token existe déjà")
        else:
            print("📋 Création de la table authtoken_token...")
            
            # Créer la table avec syntaxe MariaDB compatible
            cursor.execute("""
                CREATE TABLE `authtoken_token` (
                    `key` VARCHAR(40) NOT NULL,
                    `created` DATETIME NOT NULL,
                    `user_id` INT NOT NULL,
                    PRIMARY KEY (`key`),
                    UNIQUE KEY `authtoken_token_user_id` (`user_id`),
                    KEY `authtoken_token_key` (`key`),
                    CONSTRAINT `authtoken_token_user_id_fk` 
                        FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            print("✅ Table authtoken_token créée avec succès")
        
        connection.commit()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur création table: {e}")
        return False

def generate_token():
    """Générer un token aléatoire"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))

def create_tokens_with_table():
    """Créer les tokens après avoir créé la table"""
    print("\n🔑 CRÉATION DES TOKENS")
    print("=" * 60)
    
    try:
        connection = pymysql.connect(
            host='localhost',
            user='jey_resume',
            password='1234',
            database='jey_resume',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        # Récupérer les utilisateurs de test
        cursor.execute("""
            SELECT `id`, `email`, `username`, `is_active`, `is_staff`
            FROM `auth_user` 
            WHERE `email` IN ('cp@test.com', 'etudiant@test.com', 'admin@test.com')
            ORDER BY `email`
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("❌ Aucun utilisateur de test trouvé")
            print("💡 Exécutez d'abord: python create_test_data.py")
            return []
        
        print(f"👥 {len(users)} utilisateurs trouvés")
        
        created_tokens = []
        
        for user_id, email, username, is_active, is_staff in users:
            print(f"\n🔧 Traitement de {email}:")
            
            # Activer l'utilisateur si nécessaire
            if not is_active:
                print(f"  ⚠️ Activation de l'utilisateur...")
                cursor.execute("UPDATE `auth_user` SET `is_active` = 1 WHERE `id` = %s", (user_id,))
            
            # Supprimer l'ancien token s'il existe
            cursor.execute("DELETE FROM `authtoken_token` WHERE `user_id` = %s", (user_id,))
            if cursor.rowcount > 0:
                print(f"  🗑️ Ancien token supprimé")
            
            # Créer un nouveau token
            new_token = generate_token()
            cursor.execute("""
                INSERT INTO `authtoken_token` (`key`, `created`, `user_id`) 
                VALUES (%s, %s, %s)
            """, (new_token, datetime.now(), user_id))
            
            print(f"  ✅ Token créé: {new_token}")
            
            # Déterminer le rôle
            if 'cp@' in email:
                role = 'CP'
            elif 'admin@' in email:
                role = 'ADMIN'
            else:
                role = 'ETUDIANT'
            
            created_tokens.append({
                'email': email,
                'username': username,
                'token': new_token,
                'user_id': user_id,
                'role': role,
                'is_staff': bool(is_staff)
            })
        
        connection.commit()
        connection.close()
        
        return created_tokens
        
    except Exception as e:
        print(f"❌ Erreur création tokens: {e}")
        return []

def test_tokens_simple(tokens):
    """Test simple des tokens sans requests"""
    print(f"\n🧪 VÉRIFICATION DES TOKENS CRÉÉS")
    print("=" * 60)
    
    try:
        connection = pymysql.connect(
            host='localhost',
            user='jey_resume',
            password='1234',
            database='jey_resume',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        for token_info in tokens:
            # Vérifier que le token existe en base
            cursor.execute("""
                SELECT t.`key`, u.`email`, u.`is_active`, t.`created`
                FROM `authtoken_token` t
                JOIN `auth_user` u ON t.`user_id` = u.`id`
                WHERE t.`key` = %s
            """, (token_info['token'],))
            
            result = cursor.fetchone()
            
            if result:
                key, email, is_active, created = result
                print(f"  ✅ {email}: Token vérifié en base")
                print(f"     Créé: {created}")
                print(f"     Utilisateur actif: {'Oui' if is_active else 'Non'}")
            else:
                print(f"  ❌ {token_info['email']}: Token non trouvé")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")

def generate_flutter_code(tokens):
    """Générer le code Flutter"""
    print(f"\n📱 CODE FLUTTER GÉNÉRÉ")
    print("=" * 60)
    
    if not tokens:
        print("❌ Aucun token disponible")
        return
    
    print("🔑 Tokens pour votre application Flutter:")
    print()
    
    # Code Dart
    flutter_code = """
// Tokens d'authentification générés automatiquement
class AuthTokens {
  static const String baseUrl = 'https://resumecours.gestionhospitaliare.site/api';
  
  // Tokens de test
"""
    
    for token_info in tokens:
        role = token_info['role'].lower()
        flutter_code += f"  static const String {role}Token = '{token_info['token']}';\n"
    
    flutter_code += """
  // Méthode pour tester l'authentification
  static Future<Map<String, dynamic>?> testAuth(String token) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/auth/user/'),
        headers: {
          'Authorization': 'Token $token',
          'Content-Type': 'application/json',
        },
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        print('Auth failed: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('Auth error: $e');
      return null;
    }
  }
  
  // Test de tous les tokens
  static Future<void> testAllTokens() async {
    print('Testing CP token...');
    await testAuth(cpToken);
    
    print('Testing Etudiant token...');
    await testAuth(etudiantToken);
    
    print('Testing Admin token...');
    await testAuth(adminToken);
  }
}
"""
    
    print(flutter_code)
    
    # Sauvegarder dans un fichier
    try:
        with open('auth_tokens_flutter.dart', 'w') as f:
            f.write(flutter_code)
        print("✅ Code Flutter sauvegardé dans: auth_tokens_flutter.dart")
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde: {e}")

def generate_curl_commands(tokens):
    """Générer les commandes curl"""
    print(f"\n📋 COMMANDES CURL POUR TESTER")
    print("=" * 60)
    
    for token_info in tokens:
        email = token_info['email']
        token = token_info['token']
        role = token_info['role']
        
        print(f"\n# Test {role} ({email}):")
        print(f"curl -H 'Authorization: Token {token}' \\")
        print(f"     https://resumecours.gestionhospitaliare.site/api/auth/user/")
        
        print(f"\n# Test sessions audio {role}:")
        print(f"curl -H 'Authorization: Token {token}' \\")
        print(f"     https://resumecours.gestionhospitaliare.site/api/courses/sessions/audio/")

def save_tokens_summary(tokens):
    """Sauvegarder un résumé des tokens"""
    print(f"\n💾 SAUVEGARDE DES TOKENS")
    print("=" * 60)
    
    try:
        # Fichier texte simple
        with open('tokens_resume_plus.txt', 'w', encoding='utf-8') as f:
            f.write("TOKENS D'AUTHENTIFICATION - RESUME+\n")
            f.write("=" * 50 + "\n")
            f.write(f"Générés le: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
            f.write(f"Serveur: https://resumecours.gestionhospitaliare.site\n\n")
            
            for token_info in tokens:
                f.write(f"{token_info['role']} - {token_info['email']}\n")
                f.write(f"Token: {token_info['token']}\n")
                f.write(f"User ID: {token_info['user_id']}\n")
                f.write("-" * 50 + "\n\n")
            
            f.write("UTILISATION DANS FLUTTER:\n")
            f.write("headers: {\n")
            f.write("  'Authorization': 'Token YOUR_TOKEN_HERE',\n")
            f.write("  'Content-Type': 'application/json',\n")
            f.write("}\n")
        
        print("✅ Résumé sauvegardé dans: tokens_resume_plus.txt")
        
        # Fichier JSON
        import json
        tokens_json = {
            'generated_at': datetime.now().isoformat(),
            'server': 'https://resumecours.gestionhospitaliare.site',
            'tokens': {token['email']: token['token'] for token in tokens}
        }
        
        with open('tokens_resume_plus.json', 'w') as f:
            json.dump(tokens_json, f, indent=2)
        
        print("✅ JSON sauvegardé dans: tokens_resume_plus.json")
        
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde: {e}")

def main():
    """Fonction principale"""
    print("🚀 CRÉATEUR DE TOKENS AVEC TABLE - RESUME+")
    print("=" * 80)
    
    try:
        # 1. Créer la table authtoken_token
        if not create_token_table():
            print("❌ Impossible de créer la table")
            return
        
        # 2. Créer les tokens
        tokens = create_tokens_with_table()
        
        if not tokens:
            print("❌ Aucun token créé")
            return
        
        # 3. Vérifier les tokens
        test_tokens_simple(tokens)
        
        # 4. Générer le code Flutter
        generate_flutter_code(tokens)
        
        # 5. Générer les commandes curl
        generate_curl_commands(tokens)
        
        # 6. Sauvegarder les tokens
        save_tokens_summary(tokens)
        
        # Résumé final
        print(f"\n" + "=" * 80)
        print("✅ TOKENS CRÉÉS AVEC SUCCÈS")
        print("=" * 80)
        
        print(f"🔑 {len(tokens)} tokens générés et vérifiés:")
        for token_info in tokens:
            print(f"  • {token_info['role']}: {token_info['email']}")
            print(f"    Token: {token_info['token']}")
        
        print(f"\n📁 Fichiers créés:")
        print(f"  • auth_tokens_flutter.dart (code Flutter)")
        print(f"  • tokens_resume_plus.txt (résumé)")
        print(f"  • tokens_resume_plus.json (format JSON)")
        
        print(f"\n💡 PROCHAINES ÉTAPES:")
        print(f"1. Copiez le code Flutter généré dans votre app")
        print(f"2. Testez avec les commandes curl affichées")
        print(f"3. Les tokens sont maintenant prêts à utiliser!")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()