# Generated by Django 5.0.1 on 2024-01-25 01:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('explanation', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='description',
            name='no',
            field=models.IntegerField(default=0, unique=True),
        ),
    ]
