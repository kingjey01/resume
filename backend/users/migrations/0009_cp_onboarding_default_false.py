# Generated manually
# 1. Change la valeur par défaut de cp_onboarding_completed à False.
# 2. Les CP/ADMIN existants sont marqués True (ils ont déjà fait l'onboarding,
#    on ne le leur re-propose pas).

from django.db import migrations, models


def set_existing_cp_onboarding_completed(apps, schema_editor):
    """Les CP/ADMIN existants ont déjà terminé leur onboarding."""
    UserProfile = apps.get_model('users', 'UserProfile')
    UserProfile.objects.filter(groupe__in=['CP', 'ADMIN']).update(
        cp_onboarding_completed=True
    )


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_userprofile_cp_onboarding_completed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='cp_onboarding_completed',
            field=models.BooleanField(
                default=False,
                help_text="Source de vérité : le CP a-t-il terminé son onboarding ?",
            ),
        ),
        migrations.RunPython(
            set_existing_cp_onboarding_completed,
            migrations.RunPython.noop,
        ),
    ]
