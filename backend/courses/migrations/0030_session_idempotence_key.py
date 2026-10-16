"""Ajoute la clé d'idempotence à Session.

POURQUOI (tâche 40, étape C) : un envoi audio de plusieurs mégaoctets peut être
interrompu — verrouillage d'écran, coupure réseau — APRÈS que le serveur a créé
la session mais AVANT que l'application n'ait reçu la réponse. L'application
rejoue alors la même tentative. Sans cette clé, le serveur créerait une SECONDE
session pour le même enregistrement.

La clé est produite par l'application, une fois par envoi, et renvoyée à
l'identique à chaque reprise : la vue d'upload retrouve la session existante et
la renvoie au lieu d'en créer une autre.

Null autorisé : les envois d'anciennes versions de l'application n'en portent
pas, et PostgreSQL autorise plusieurs NULL dans un index unique.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0029_professeurfilieres_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='idempotence_key',
            field=models.CharField(
                blank=True,
                help_text="Identifiant d'envoi fourni par l'application, contre les doublons",
                max_length=64,
                null=True,
                unique=True,
            ),
        ),
    ]
