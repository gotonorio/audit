# Generated by Django 5.0.3 on 2024-03-18 04:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('record', '0006_claimdata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='claimdata',
            name='claim_type',
            field=models.CharField(choices=[('未収金', '未収金'), ('前受金', '前受金'), ('滞納金', '滞納金')], default='未収金', max_length=4, verbose_name='請求種別'),
        ),
    ]
