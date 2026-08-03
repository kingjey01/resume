from django.db import migrations, models


def migrate_fk_to_m2m(apps, schema_editor):
    """Copie les FK existantes vers les nouvelles tables M2M."""
    Course = apps.get_model('courses', 'Course')
    for course in Course.objects.all():
        if course.universite_fk_id:
            course.universites.add(course.universite_fk_id)
        if course.filiere_fk_id:
            course.filieres.add(course.filiere_fk_id)
        if course.promotion_fk_id:
            course.promotions.add(course.promotion_fk_id)


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0018_user_personalized_exercises'),
    ]

    operations = [
        # 1. Ajouter les tables M2M
        migrations.AddField(
            model_name='course',
            name='universites',
            field=models.ManyToManyField(blank=True, related_name='courses', to='courses.universite'),
        ),
        migrations.AddField(
            model_name='course',
            name='filieres',
            field=models.ManyToManyField(blank=True, related_name='courses', to='courses.filiere'),
        ),
        migrations.AddField(
            model_name='course',
            name='promotions',
            field=models.ManyToManyField(blank=True, related_name='courses', to='courses.promotion'),
        ),
        # 2. Copier les données des FK vers les M2M
        migrations.RunPython(migrate_fk_to_m2m, migrations.RunPython.noop),
        # 3. Supprimer les anciens champs FK
        migrations.RemoveField(
            model_name='course',
            name='universite_fk',
        ),
        migrations.RemoveField(
            model_name='course',
            name='filiere_fk',
        ),
        migrations.RemoveField(
            model_name='course',
            name='promotion_fk',
        ),
    ]
