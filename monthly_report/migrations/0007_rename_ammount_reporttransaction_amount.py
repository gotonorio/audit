# Generated by Django 5.1 on 2024-09-04 04:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('monthly_report', '0006_reporttransaction_is_manualinput'),
    ]

    operations = [
        migrations.RenameField(
            model_name='reporttransaction',
            old_name='ammount',
            new_name='amount',
        ),
    ]
