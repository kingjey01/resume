from django.db import migrations

def migrate_existing_relations(apps, schema_editor):
    """
    Migre les relations existantes vers les nouvelles tables de liaison ManyToMany.
    """
    # Récupérer les modèles
    Universite = apps.get_model('courses', 'Universite')
    Filiere = apps.get_model('courses', 'Filiere')
    Promotion = apps.get_model('courses', 'Promotion')
    UniversiteFiliere = apps.get_model('courses', 'UniversiteFiliere')
    FilierePromotion = apps.get_model('courses', 'FilierePromotion')
    
    print("\nDébut de la migration des relations existantes...")
    
    # 1. Migrer les relations Université-Filière (si vous avez un champ filiere dans Universite)
    try:
        universites = Universite.objects.all()
        uf_created = 0
        
        for universite in universites:
            if hasattr(universite, 'filiere'):
                # Créer la relation dans la table de liaison
                UniversiteFiliere.objects.get_or_create(
                    universite=universite,
                    filiere=universite.filiere
                )
                uf_created += 1
        
        print(f"{uf_created} relations Université-Filière créées.")
    except Exception as e:
        print(f"Erreur lors de la migration des relations Université-Filière: {e}")
    
    # 2. Migrer les relations Filière-Promotion (si vous avez un champ promotion dans Filiere)
    try:
        filieres = Filiere.objects.all()
        fp_created = 0
        
        for filiere in filieres:
            if hasattr(filiere, 'promotion'):
                # Créer la relation dans la table de liaison
                FilierePromotion.objects.get_or_create(
                    filiere=filiere,
                    promotion=filiere.promotion
                )
                fp_created += 1
        
        print(f"{fp_created} relations Filière-Promotion créées.")
    except Exception as e:
        print(f"Erreur lors de la migration des relations Filière-Promotion: {e}")
    
    print("Migration des relations existantes terminée avec succès!")

class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_universitefiliere_filierepromotion_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_existing_relations),
    ]
