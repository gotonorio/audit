# Generated by Django 5.0 on 2023-12-12 11:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("control", "0002_controlrecord_to_offset"),
        ("record", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="controlrecord",
            name="to_offset",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="record.himoku",
                verbose_name="費目名",
            ),
        ),
    ]
