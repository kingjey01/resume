# Generated manually - Migration pour convertir UniversiteFiliere vers M2M auto

from django.db import migrations, models


def copy_universite_filiere_to_m2m(apps, schema_editor):
    """Copie les relations UniversiteFiliere existantes vers le nouveau M2M"""
    Universite = apps.get_model('courses', 'Universite')
    UniversiteFiliere = apps.get_model('courses', 'UniversiteFiliere')
    
    for uf in UniversiteFiliere.objects.all().select_related('universite', 'filiere'):
        universite = uf.universite
        filiere = uf.filiere
        if filiere and universite:
            universite.filieres.add(filiere)


def restore_universite_filiere_from_m2m(apps, schema_editor):
    """Restaure les relations depuis le M2M vers le modèle UniversiteFiliere (reverse)"""
    Universite = apps.get_model('courses', 'Universite')
    UniversiteFiliere = apps.get_model('courses', 'UniversiteFiliere')
    
    for universite in Universite.objects.all().prefetch_related('filieres'):
        for filiere in universite.filieres.all():
            UniversiteFiliere.objects.get_or_create(
                universite=universite,
                filiere=filiere
            )


class Migration(migrations.Migration):
    dependencies = [
        ('courses', '0016_filiere_promotions_m2m'),
    ]

    operations = [
        # 1. Supprimer l'ancien champ M2M avec through
        migrations.RemoveField(
            model_name='universite',
            name='filieres',
        ),
        
        # 2. Ajouter le nouveau champ M2M sans through
        migrations.AddField(
            model_name='universite',
            name='filieres',
            field=models.ManyToManyField(
                blank=True,
                related_name='universites',
                to='courses.Filiere',
            ),
        ),
        
        # 3. Copier les données
        migrations.RunPython(
            copy_universite_filiere_to_m2m,
            restore_universite_filiere_from_m2m
        ),
        
        # 4. Supprimer le modèle UniversiteFiliere
        migrations.DeleteModel(
            name='UniversiteFiliere',
        ),
    ]
