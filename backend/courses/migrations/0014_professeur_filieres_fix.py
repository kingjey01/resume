# Generated manually to fix M2M through migration issue
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0013_make_professeur_optional'),
    ]

    operations = [
        # Use SeparateDatabaseAndState to avoid altering the M2M field in DB
        # The table courses_professeur_filieres already exists
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # Add ProfesseurFilieres as unmanaged through model (state only)
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
                # No database changes needed - table already exists
            ],
        ),
    ]
