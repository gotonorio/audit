# Generated by Django 5.0 on 2023-12-19 07:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("record", "0003_himoku_is_default_himoku_default_himoku_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="is_approval",
            field=models.BooleanField(default=True, verbose_name="承認必要"),
        ),
    ]