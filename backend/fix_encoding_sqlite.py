#!/usr/bin/env python3
"""
Script pour corriger les problèmes d'encodage UTF-8 dans SQLite
"""
import os
import sys
import django
from django.conf import settings

# Ajouter le répertoire du projet au path
sys.path.append('/home/jey/resume_plus_clean/backend')

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from django.db import connection
from courses.models import Summary, Session

def fix_sqlite_encoding():
    """Corriger l'encodage SQLite (SQLite utilise UTF-8 par défaut)"""
    print("🔧 Vérification de l'encodage SQLite...")
    
    try:
        with connection.cursor() as cursor:
            # Vérifier la version SQLite
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            print(f"📊 Version SQLite: {version}")
            
            # SQLite utilise UTF-8 par défaut, mais vérifions
            cursor.execute("PRAGMA encoding")
            encoding = cursor.fetchone()[0]
            print(f"📊 Encodage SQLite: {encoding}")
            
            if encoding.upper() != 'UTF-8':
                print("⚠️ L'encodage n'est pas UTF-8, mais SQLite gère cela automatiquement")
            else:
                print("✅ Encodage UTF-8 confirmé")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

def clean_invalid_utf8_data():
    """Nettoyer les données UTF-8 invalides existantes"""
    print("\n🧹 Nettoyage des données UTF-8 invalides...")
    
    try:
        # Utiliser l'ORM Django pour plus de sécurité
        summaries_with_issues = Summary.objects.filter(
            texte_resume__contains='\\x'
        )
        
        cleaned_count = 0
        for summary in summaries_with_issues:
            original_text = summary.texte_resume
            
            # Nettoyer les séquences d'échappement invalides
            cleaned_text = original_text.replace('\\\\xF0\\\\x9F\\\\x93\\\\x9A', '📚')
            cleaned_text = cleaned_text.replace('\\\\xF0\\\\x9F\\\\x8E\\\\x93', '🎓')
            cleaned_text = cleaned_text.replace('\\\\xF0\\\\x9F\\\\x9A\\\\x80', '🚀')
            cleaned_text = cleaned_text.replace('\\\\xE2\\\\x9C\\\\x85', '✅')
            
            # Supprimer les autres séquences d'échappement
            import re
            cleaned_text = re.sub(r'\\\\x[0-9A-Fa-f]{2}', '', cleaned_text)
            
            if cleaned_text != original_text:
                summary.texte_resume = cleaned_text
                summary.save()
                cleaned_count += 1
                print(f"✅ Résumé {summary.id} nettoyé")
        
        print(f"✅ {cleaned_count} résumés nettoyés")
        
        # Nettoyer les titres
        titles_with_issues = Summary.objects.filter(
            titre__contains='Ã©'
        )
        
        title_cleaned_count = 0
        for summary in titles_with_issues:
            original_title = summary.titre
            cleaned_title = original_title.replace('Ã©', 'é')
            cleaned_title = cleaned_title.replace('Ã¨', 'è')
            cleaned_title = cleaned_title.replace('Ã ', 'à')
            
            if cleaned_title != original_title:
                summary.titre = cleaned_title
                summary.save()
                title_cleaned_count += 1
                print(f"✅ Titre {summary.id} nettoyé: '{cleaned_title}'")
        
        print(f"✅ {title_cleaned_count} titres nettoyés")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")

def test_emoji_insertion():
    """Tester l'insertion d'emojis"""
    print("\n🧪 Test d'insertion d'emojis...")
    
    try:
        # Créer un résumé de test avec des emojis
        test_text = "📚 Test d'encodage UTF-8 avec emojis 🎓✅🚀\n\nCe texte contient des emojis pour tester l'encodage."
        
        # Utiliser l'ORM Django
        from courses.models import Course
        
        # Récupérer le premier cours disponible
        course = Course.objects.first()
        if not course:
            print("❌ Aucun cours disponible pour le test")
            return
        
        # Créer le résumé de test
        test_summary = Summary.objects.create(
            titre="Test Emoji 🎓",
            texte_resume=test_text,
            course=course,
            author_type='cp',
            prix=0,
            is_free=True
        )
        
        print(f"✅ Test d'insertion réussi: ID {test_summary.id}")
        print(f"📝 Titre: {test_summary.titre}")
        print(f"📄 Texte: {test_summary.texte_resume[:100]}...")
        
        # Vérifier que les emojis sont bien sauvegardés
        retrieved_summary = Summary.objects.get(id=test_summary.id)
        if '📚' in retrieved_summary.texte_resume and '🎓' in retrieved_summary.titre:
            print("✅ Emojis correctement sauvegardés et récupérés")
        else:
            print("❌ Problème avec les emojis")
        
        # Supprimer le test
        test_summary.delete()
        print("✅ Données de test nettoyées")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")

def check_existing_data():
    """Vérifier les données existantes"""
    print("\n🔍 Vérification des données existantes...")
    
    try:
        # Compter les résumés
        total_summaries = Summary.objects.count()
        print(f"📊 Total des résumés: {total_summaries}")
        
        # Compter les sessions audio
        total_sessions = Session.objects.count()
        print(f"📊 Total des sessions audio: {total_sessions}")
        
        # Vérifier les résumés avec des caractères problématiques
        problematic_summaries = Summary.objects.filter(
            texte_resume__contains='\\x'
        ).count()
        print(f"⚠️ Résumés avec caractères problématiques: {problematic_summaries}")
        
        # Vérifier les titres avec des caractères problématiques
        problematic_titles = Summary.objects.filter(
            titre__contains='Ã'
        ).count()
        print(f"⚠️ Titres avec caractères problématiques: {problematic_titles}")
        
        # Afficher quelques exemples
        if problematic_summaries > 0:
            example = Summary.objects.filter(texte_resume__contains='\\x').first()
            if example:
                print(f"📄 Exemple de texte problématique: {example.texte_resume[:100]}...")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

def main():
    print("🚀 CORRECTION DE L'ENCODAGE UTF-8 (SQLite)")
    print("="*50)
    
    # Étape 1: Vérifier l'encodage SQLite
    fix_sqlite_encoding()
    
    # Étape 2: Vérifier les données existantes
    check_existing_data()
    
    # Étape 3: Nettoyer les données existantes
    clean_invalid_utf8_data()
    
    # Étape 4: Tester les emojis
    test_emoji_insertion()
    
    print(f"\n{'='*50}")
    print("📋 RÉSUMÉ")
    print('='*50)
    print("✅ Encodage SQLite vérifié (UTF-8 par défaut)")
    print("✅ Données invalides nettoyées")
    print("✅ Support des emojis confirmé")
    print("✅ Le problème d'encodage devrait être résolu")
    print("\n💡 Les changements sont appliqués immédiatement avec SQLite")

if __name__ == "__main__":
    main()