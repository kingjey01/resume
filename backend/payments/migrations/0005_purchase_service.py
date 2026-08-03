from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_alter_purchase_summary'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='service',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='purchases',
                to='payments.service',
            ),
        ),
    ]
