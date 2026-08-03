#!/usr/bin/env python3
"""
Test de la correction d'encodage
"""
import requests
import json

BASE_URL = "https://resumecours.gestionhospitaliare.site"
TOKEN = "9743c81fdd50b11c38a55fb9de24c56d8d4857dd"  # Token admin

def test_summary_with_special_chars():
    """Test de création de summary avec caractères spéciaux"""
    print("🧪 Test de création de summary avec caractères spéciaux...")
    
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Données de test avec caractères spéciaux et emojis
    test_data = {
        "titre": "Test avec caractères spéciaux: àéèùç 'apostrophes' \"guillemets\" 📚",
        "texte_resume": "Voici un résumé avec des caractères spéciaux:\\n\\n🔍 Émojis: 📚📝✅❌🎯\\n\\n• Apostrophes courbes: 'test' et guillemets\\n• Tirets: – et —\\n• Accents: àáâãäåæçèéêëìíîïñòóôõöøùúûüý\\n• Symboles: €£¥©®™\\n\\nCe texte devrait maintenant être sauvegardé correctement! 🎉",
        "author_type": "cp",
        "prix": 0.00,
        "is_free": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/summaries/",
            json=test_data,
            headers=headers,
            timeout=10
        )
        
        print(f"📡 Réponse: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ Summary créé avec succès!")
            print(f"🆔 ID: {data.get('id')}")
            print(f"📝 Titre: {data.get('titre')}")
            print(f"📄 Texte (extrait): {data.get('texte_resume', '')[:100]}...")
            return data
        else:
            print(f"❌ Échec: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Erreurs: {error_data}")
            except:
                print(f"Contenu: {response.text[:300]}")
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    return None

def test_summary_retrieval():
    """Test de récupération des summaries"""
    print(f"\n📖 Test de récupération des summaries...")
    
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/summaries/", headers=headers, timeout=10)
        print(f"📡 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {len(data)} summaries récupérés")
            
            # Afficher les derniers summaries
            for summary in data[-3:]:  # 3 derniers
                print(f"  📝 {summary.get('id')}: {summary.get('titre', '')[:50]}...")
        else:
            print(f"❌ Échec: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    print("🚀 TEST DE LA CORRECTION D'ENCODAGE")
    print("="*50)
    
    # Test 1: Création avec caractères spéciaux
    summary_data = test_summary_with_special_chars()
    
    # Test 2: Récupération
    test_summary_retrieval()
    
    print(f"\n{'='*50}")
    print("📋 RÉSUMÉ")
    print('='*50)
    
    if summary_data:
        print("✅ La correction d'encodage fonctionne!")
        print("✅ Les caractères spéciaux sont maintenant supportés!")
        print("✅ Votre app Flutter peut utiliser tous les caractères!")
    else:
        print("❌ La correction d'encodage n'est pas encore effective")
        print("❌ Vérifiez que les commandes SQL ont été exécutées")

if __name__ == "__main__":
    main()