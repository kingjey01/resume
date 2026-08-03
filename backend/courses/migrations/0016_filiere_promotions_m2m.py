from django.db import migrations, models


def copy_through_to_auto(apps, schema_editor):
    """Recopie les associations Filière↔Promotion de la table `through`
    (FilierePromotion) vers la nouvelle table M2M automatique."""
    FilierePromotion = apps.get_model('courses', 'FilierePromotion')
    for fp in FilierePromotion.objects.all():
        fp.filiere.promotions.add(fp.promotion)


def copy_auto_to_through(apps, schema_editor):
    """Reverse: recopie les associations de la table M2M auto vers la table
    `through` FilierePromotion (recréée par DeleteModel.reverse)."""
    Filiere = apps.get_model('courses', 'Filiere')
    FilierePromotion = apps.get_model('courses', 'FilierePromotion')
    for filiere in Filiere.objects.all():
        for promotion in filiere.promotions.all():
            FilierePromotion.objects.get_or_create(filiere=filiere, promotion=promotion)


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0015_merge_20260523_2104'),
    ]

    operations = [
        # 1. Retire le champ M2M basé sur `through=FilierePromotion` (aucune table propre,
        #    donc pas de perte de données : les associations restent dans FilierePromotion).
        migrations.RemoveField(
            model_name='filiere',
            name='promotions',
        ),
        # 2. Ajoute le nouveau M2M auto → crée la table `courses_filiere_promotions` (vide).
        migrations.AddField(
            model_name='filiere',
            name='promotions',
            field=models.ManyToManyField(blank=True, related_name='filieres', to='courses.promotion'),
        ),
        # 3. Copie les associations existantes de FilierePromotion vers la nouvelle table.
        migrations.RunPython(copy_through_to_auto, copy_auto_to_through),
        # 4. Supprime l'ancienne table `through` désormais inutilisée.
        migrations.DeleteModel(name='FilierePromotion'),
    ]
