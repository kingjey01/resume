# Tâche 57 — le quota QCM se compte en PACKS (3 niveaux, 24 questions).
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0030_session_idempotence_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='quota_periode_debut',
            field=models.DateTimeField(
                blank=True,
                help_text=(
                    "Début de la période d'abonnement pour laquelle le pack "
                    'QCM de ce résumé a été consommé'
                ),
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='userpersonalizedexercise',
            name='quota_periode_debut',
            field=models.DateTimeField(
                blank=True,
                help_text=(
                    "Début de la période d'abonnement pour laquelle le pack "
                    'QCM de ce résumé a été consommé'
                ),
                null=True,
            ),
        ),
        migrations.AddIndex(
            model_name='exercise',
            index=models.Index(
                fields=['created_by', 'summary', 'quota_periode_debut'],
                name='courses_ex_qcm_pack_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='userpersonalizedexercise',
            index=models.Index(
                fields=['user', 'summary', 'quota_periode_debut'],
                name='courses_perso_qcm_pack_idx',
            ),
        ),
    ]
