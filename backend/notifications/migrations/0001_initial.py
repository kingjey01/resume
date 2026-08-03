from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0014_professeur_filieres_fix'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AppNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('notification_type', models.CharField(
                    choices=[
                        ('new_summary', 'Nouveau résumé'),
                        ('summary_validated', 'Résumé validé'),
                        ('new_exercise', 'Nouvel exercice'),
                        ('system', 'Système'),
                        ('promo', 'Promotion'),
                        ('payment', 'Paiement'),
                        ('general', 'Général'),
                    ],
                    default='general',
                    max_length=30,
                )),
                ('summary_id', models.IntegerField(blank=True, null=True)),
                ('course_id', models.IntegerField(blank=True, null=True)),
                ('image_url', models.URLField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sender', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='sent_notifications',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('target_filiere', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notifications',
                    to='courses.filiere',
                )),
                ('target_promotion', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notifications',
                    to='courses.promotion',
                )),
                ('target_universite', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notifications',
                    to='courses.universite',
                )),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserDevice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fcm_token', models.TextField(unique=True)),
                ('device_type', models.CharField(
                    choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')],
                    default='android',
                    max_length=10,
                )),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='devices',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Appareil Utilisateur',
                'verbose_name_plural': 'Appareils Utilisateurs',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='UserNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_read', models.BooleanField(default=False)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('delivered', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('notification', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='user_notifications',
                    to='notifications.appnotification',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='user_notifications',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Notification Utilisateur',
                'verbose_name_plural': 'Notifications Utilisateurs',
                'ordering': ['-created_at'],
                'unique_together': {('user', 'notification')},
            },
        ),
    ]
