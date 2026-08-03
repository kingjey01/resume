#!/usr/bin/env python3
"""
Créateur de tokens simple - Sans dépendances externes
"""

import pymysql
import secrets
import string
from datetime import datetime

def generate_token():
    """Générer un token aléatoire de 40 caractères"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))

def create_auth_tokens():
    """Créer des tokens d'authentification directement en MySQL"""
    print("🔑 CRÉATION DE TOKENS D'AUTHENTIFICATION")
    print("=" * 60)
    
    try:
        # Connexion MySQL
        print("🔌 Connexion à MySQL...")
        connection = pymysql.connect(
            host='localhost',
            user='jey_resume',
            password='1234',
            database='jey_resume',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        print("✅ Connexion MySQL réussie")
        
        # Vérifier les utilisateurs existants
        print("\n👥 Vérification des utilisateurs...")
        cursor.execute("""
            SELECT id, email, username, is_active, is_staff
            FROM auth_user 
            WHERE email IN ('cp@test.com', 'etudiant@test.com', 'admin@test.com')
            ORDER BY email
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("❌ Aucun utilisateur de test trouvé")
            print("💡 Exécutez d'abord: python create_test_data.py")
            return []
        
        print(f"📊 {len(users)} utilisateurs trouvés")
        
        # Créer les tokens
        created_tokens = []
        
        for user_id, email, username, is_active, is_staff in users:
            print(f"\n🔧 Traitement de {email}:")
            
            if not is_active:
                print(f"  ⚠️ Utilisateur inactif - activation...")
                cursor.execute("UPDATE auth_user SET is_active = 1 WHERE id = %s", (user_id,))
            
            # Supprimer l'ancien token
            cursor.execute("DELETE FROM authtoken_token WHERE user_id = %s", (user_id,))
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(f"  🗑️ Ancien token supprimé")
            
            # Créer un nouveau token
            new_token = generate_token()
            cursor.execute("""
                INSERT INTO authtoken_token (key, created, user_id) 
                VALUES (%s, %s, %s)
            """, (new_token, datetime.now(), user_id))
            
            print(f"  ✅ Nouveau token créé")
            print(f"  🔑 Token: {new_token}")
            
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
        
        # Valider les changements
        connection.commit()
        print(f"\n💾 Changements sauvegardés en base")
        
        connection.close()
        
        return created_tokens
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []

def verify_tokens_in_database(tokens):
    """Vérifier que les tokens sont bien en base"""
    print(f"\n🔍 VÉRIFICATION DES TOKENS EN BASE")
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
            cursor.execute("""
                SELECT t.key, u.email, u.is_active, t.created
                FROM authtoken_token t
                JOIN auth_user u ON t.user_id = u.id
                WHERE t.key = %s
            """, (token_info['token'],))
            
            result = cursor.fetchone()
            
            if result:
                key, email, is_active, created = result
                print(f"  ✅ {email}: Token vérifié")
                print(f"     Créé: {created}")
                print(f"     Actif: {'Oui' if is_active else 'Non'}")
            else:
                print(f"  ❌ {token_info['email']}: Token non trouvé en base")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        return False

def generate_test_commands(tokens):
    """Générer des commandes de test"""
    print(f"\n📋 COMMANDES DE TEST")
    print("=" * 60)
    
    if not tokens:
        print("❌ Aucun token disponible")
        return
    
    print("🧪 Commandes curl pour tester:")
    
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

def generate_flutter_config(tokens):
    """Générer la configuration Flutter"""
    print(f"\n📱 CONFIGURATION FLUTTER")
    print("=" * 60)
    
    if not tokens:
        print("❌ Aucun token disponible")
        return
    
    print("🔑 Tokens pour votre application Flutter:")
    print()
    
    for token_info in tokens:
        print(f"// {token_info['role']} - {token_info['email']}")
        print(f"const String {token_info['role'].lower()}Token = '{token_info['token']}';")
        print()
    
    print("📝 Code Flutter d'exemple:")
    print("""
class AuthTokens {
  // Tokens générés automatiquement""")
    
    for token_info in tokens:
        role = token_info['role'].lower()
        print(f"  static const String {role}Token = '{token_info['token']}';")
    
    print("""
  // Méthode pour tester l'authentification
  static Future<bool> testAuth(String token) async {
    try {
      final response = await http.get(
        Uri.parse('https://resumecours.gestionhospitaliare.site/api/auth/user/'),
        headers: {
          'Authorization': 'Token \$token',
          'Content-Type': 'application/json',
        },
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Auth error: \$e');
      return false;
    }
  }
}
""")

def save_tokens_to_file(tokens):
    """Sauvegarder les tokens dans un fichier"""
    print(f"\n💾 SAUVEGARDE DES TOKENS")
    print("=" * 60)
    
    try:
        import json
        
        # Préparer les données
        tokens_data = {
            'generated_at': datetime.now().isoformat(),
            'server': 'https://resumecours.gestionhospitaliare.site',
            'tokens': {}
        }
        
        for token_info in tokens:
            tokens_data['tokens'][token_info['email']] = {
                'token': token_info['token'],
                'role': token_info['role'],
                'user_id': token_info['user_id'],
                'username': token_info['username']
            }
        
        # Sauvegarder en JSON
        with open('auth_tokens.json', 'w') as f:
            json.dump(tokens_data, f, indent=2)
        
        print("✅ Tokens sauvegardés dans: auth_tokens.json")
        
        # Sauvegarder aussi en format simple
        with open('tokens_simple.txt', 'w') as f:
            f.write("TOKENS D'AUTHENTIFICATION RESUME+\n")
            f.write("=" * 40 + "\n\n")
            
            for token_info in tokens:
                f.write(f"{token_info['role']} ({token_info['email']}):\n")
                f.write(f"Token: {token_info['token']}\n\n")
        
        print("✅ Tokens sauvegardés dans: tokens_simple.txt")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 CRÉATEUR DE TOKENS SIMPLE - RESUME+")
    print("=" * 80)
    
    try:
        # 1. Créer les tokens
        tokens = create_auth_tokens()
        
        if not tokens:
            print("\n❌ Aucun token créé")
            return
        
        # 2. Vérifier en base
        verify_tokens_in_database(tokens)
        
        # 3. Générer les commandes de test
        generate_test_commands(tokens)
        
        # 4. Générer la config Flutter
        generate_flutter_config(tokens)
        
        # 5. Sauvegarder les tokens
        save_tokens_to_file(tokens)
        
        # Résumé final
        print(f"\n" + "=" * 80)
        print("✅ TOKENS CRÉÉS AVEC SUCCÈS")
        print("=" * 80)
        
        print(f"🔑 {len(tokens)} tokens générés:")
        for token_info in tokens:
            print(f"  • {token_info['role']}: {token_info['email']}")
        
        print(f"\n💡 PROCHAINES ÉTAPES:")
        print(f"1. Copiez les tokens dans votre app Flutter")
        print(f"2. Testez avec les commandes curl affichées")
        print(f"3. Vérifiez les fichiers sauvegardés:")
        print(f"   - auth_tokens.json")
        print(f"   - tokens_simple.txt")
        
        print(f"\n🎯 TOKENS PRÊTS À UTILISER:")
        for token_info in tokens:
            print(f"  {token_info['email']}: {token_info['token']}")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()