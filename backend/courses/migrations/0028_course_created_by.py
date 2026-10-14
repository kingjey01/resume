from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Ajoute l'auteur d'un cours.

    POURQUOI (2026-10-14) : `CanModifyObject` autorise « le créateur » en
    testant `obj.author_user` — un champ qui n'existe que sur les RÉSUMÉS.
    Sur un Course, ce test était donc toujours faux : seul un administrateur
    pouvait supprimer un cours, et tout autre compte recevait le 403 par défaut
    de Django REST Framework, « Vous n'avez pas la permission d'effectuer cette
    action » — y compris l'auteur du cours.

    Les cours existants restent avec `created_by` à NULL : pour eux, la
    suppression demeure réservée aux administrateurs, c'est-à-dire la règle qui
    s'appliquait déjà de fait.
    """

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0027_remove_userpersonalizedattempt_results_detail_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='created_courses',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
