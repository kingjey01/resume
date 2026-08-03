# Manual fix migration - removes through= from Professeur.filieres M2M
# This migration does NOT alter the database, it only updates Django's state.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_add_course_fk_fields'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='ProfesseurFilieres',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('professeur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.professeur')),
                        ('filiere', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.filiere')),
                    ],
                    options={
                        'db_table': 'courses_professeur_filieres',
                        'managed': False,
                    },
                ),
            ],
            database_operations=[
                # Intentionally empty - table already exists, do not ALTER the M2M field
            ],
        ),
    ]
