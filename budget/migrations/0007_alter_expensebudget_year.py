# Generated by Django 5.1.4 on 2025-01-18 05:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0006_delete_incomebudget'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expensebudget',
            name='year',
            field=models.IntegerField(default=2025, verbose_name='西暦'),
        ),
    ]
