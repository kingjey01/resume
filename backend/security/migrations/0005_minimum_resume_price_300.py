# Tâche 57 : le prix minimum des résumés passe de 3 000 à 300 FC.
from decimal import Decimal

from django.db import migrations, models


def abaisser_seuil_herite(apps, schema_editor):
    """Aligne les configurations existantes encore à l'ancien seuil de 3 000 FC.

    La valeur est configurable dans l'admin ; on ne touche donc qu'aux lignes
    qui portent encore EXACTEMENT l'ancienne valeur par défaut. Un seuil
    personnalisé par l'administrateur est conservé.
    """
    ResumePricingConfig = apps.get_model('security', 'ResumePricingConfig')
    ResumePricingConfig.objects.filter(
        minimum_resume_price=Decimal('3000.00')
    ).update(minimum_resume_price=Decimal('300.00'))


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0004_appversion_resumepricingconfig'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resumepricingconfig',
            name='minimum_resume_price',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('300.00'),
                help_text=(
                    'Seuil en Francs Congolais. En dessous, '
                    'la création du résumé est refusée.'
                ),
                max_digits=10,
                verbose_name='Prix minimum (CDF)',
            ),
        ),
        migrations.RunPython(abaisser_seuil_herite, migrations.RunPython.noop),
    ]
