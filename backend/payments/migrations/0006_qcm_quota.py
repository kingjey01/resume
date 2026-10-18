# Generated manually for tâche 57 — quota mensuel de générations QCM.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_purchase_service'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='quota_qcm_mensuel',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Générations complètes de QCM (3 niveaux) par période de 30 jours (0 = illimité)',
            ),
        ),
        migrations.AddField(
            model_name='service',
            name='plafond_qcm_journalier',
            field=models.PositiveIntegerField(
                default=0,
                help_text=(
                    'Générations complètes de QCM autorisées par jour. '
                    '0 = plafond dérivé du quota mensuel (quota / 30, minimum 1).'
                ),
            ),
        ),
        migrations.AddField(
            model_name='abonnement',
            name='quota_qcm_mensuel',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Générations complètes de QCM (3 niveaux) par période de 30 jours (0 = illimité)',
            ),
        ),
        migrations.AddField(
            model_name='abonnement',
            name='plafond_qcm_journalier',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Générations complètes de QCM autorisées par jour (0 = dérivé du mensuel)',
            ),
        ),
        migrations.AddField(
            model_name='abonnement',
            name='quota_qcm_consomme',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Packs de QCM consommés sur la période courante',
            ),
        ),
        migrations.AddField(
            model_name='abonnement',
            name='quota_qcm_periode_debut',
            field=models.DateTimeField(
                blank=True,
                help_text='Début de la période de consommation courante (30 jours)',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='abonnement',
            name='quota_qcm_jour',
            field=models.DateField(
                blank=True,
                help_text='Jour du compteur journalier courant',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='abonnement',
            name='quota_qcm_jour_consomme',
            field=models.PositiveIntegerField(
                default=0,
                help_text="Packs de QCM consommés aujourd'hui",
            ),
        ),
    ]
