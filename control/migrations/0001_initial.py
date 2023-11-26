# Generated by Django 4.2.7 on 2023-11-25 11:29

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ControlRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tmp_user_flg",
                    models.BooleanField(default=False, verbose_name="仮登録"),
                ),
                (
                    "annual_management_fee",
                    models.IntegerField(default=0, verbose_name="管理費収入額"),
                ),
                (
                    "annual_greenspace_fee",
                    models.IntegerField(default=0, verbose_name="緑地維持管理費収入額"),
                ),
            ],
        ),
    ]