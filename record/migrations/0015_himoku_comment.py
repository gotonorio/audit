# Generated by Django 5.1.4 on 2025-01-21 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('record', '0014_himoku_is_community'),
    ]

    operations = [
        migrations.AddField(
            model_name='himoku',
            name='comment',
            field=models.CharField(default='', max_length=64, verbose_name='備考'),
        ),
    ]