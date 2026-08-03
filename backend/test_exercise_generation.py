"""Script pour tester la génération d'exercices QCM"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_backend.settings')
django.setup()

from django.conf import settings
from courses.models import Summary
from courses.exercise_generator import ExerciseGenerator

# --- Configuration ---
# Mettez l'ID d'un résumé existant et validé. Si None, le script en cherche un.
SUMMARY_ID_TO_TEST = None 
# -------------------


def run_test():
    print("--- Début du test de génération d'exercices QCM ---")

    # 1. Vérifier la clé d'API
    api_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
    if not api_key:
        print("🟡 AVERTISSEMENT: DEEPSEEK_API_KEY n'est pas configurée.")
        print("   La génération utilisera des questions de test (mock).")
    else:
        print(f"🟢 Clé d'API DeepSeek trouvée: ...{api_key[-4:]}")

    # 2. Trouver un résumé à tester
    summary = None
    if SUMMARY_ID_TO_TEST:
        try:
            summary = Summary.objects.get(id=SUMMARY_ID_TO_TEST, is_validated=True)
            print(f"🎯 Utilisation du résumé spécifié: ID={summary.id}, Titre='{summary.titre}'")
        except Summary.DoesNotExist:
            print(f"❌ ERREUR: Résumé avec ID={SUMMARY_ID_TO_TEST} non trouvé ou non validé.")
            return
    else:
        # Chercher le premier résumé validé avec un texte suffisant
        summary = Summary.objects.filter(is_validated=True, texte_resume__isnull=False).exclude(texte_resume__exact='').first()
        if summary:
            print(f"🎯 Résumé trouvé pour le test: ID={summary.id}, Titre='{summary.titre}'")
        else:
            print("❌ ERREUR: Aucun résumé validé avec du contenu textuel n'a été trouvé.")
            print("   Veuillez valider un résumé via l'application ou en créer un.")
            return

    # 3. Lancer la génération
    print("\n🔄 Lancement de la génération... (peut prendre jusqu'à 30 secondes)")
    generator = ExerciseGenerator()
    exercise = generator.generate_exercises_for_summary(summary.id)

    # 4. Analyser le résultat
    if not exercise:
        print("\n❌ ÉCHEC: La fonction de génération n'a retourné aucun exercice.")
        print("   Vérifiez les logs du serveur pour plus de détails (erreurs de connexion, etc.).")
        return

    if exercise.status == 'failed':
        print(f"\n❌ ÉCHEC: L'exercice (ID={exercise.id}) a le statut 'failed'.")
        print("   Cela signifie probablement que l'appel à l'API a échoué et que le mode mock a aussi eu un problème.")
    elif exercise.status == 'completed':
        question_count = exercise.questions.count()
        print(f"\n✅ SUCCÈS: Exercice (ID={exercise.id}) généré avec {question_count} questions.")
        
        # Vérifier si ce sont des questions mock
        first_question_text = exercise.questions.first().question_text if question_count > 0 else ""
        if "sujet principal abordé" in first_question_text:
            print("   ℹ️ INFO: Les questions générées sont des questions de TEST (mock).")
            print("   L'appel à l'API DeepSeek a probablement échoué (timeout, erreur API, etc.).")
        else:
            print("   ✨ INFO: Les questions semblent avoir été générées par l'IA DeepSeek.")
    else:
        print(f"\n🟡 STATUT INATTENDU: L'exercice (ID={exercise.id}) a le statut '{exercise.status}'.")

    print("\n--- Test terminé ---")

if __name__ == '__main__':
    run_test()
