# Generated by Django 4.2.7 on 2023-11-25 11:29

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Payment",
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
                    "payment_date",
                    models.DateField(
                        default=django.utils.timezone.now, verbose_name="支払日"
                    ),
                ),
                (
                    "payment_destination",
                    models.CharField(
                        blank=True, default="", max_length=32, verbose_name="支払先"
                    ),
                ),
                ("payment", models.IntegerField(default=0, verbose_name="金額")),
                (
                    "summary",
                    models.CharField(
                        blank=True, default="", max_length=64, verbose_name="摘要"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PaymentCategory",
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
                    "payment_name",
                    models.CharField(max_length=32, verbose_name="支払い種別名"),
                ),
                ("comment", models.TextField(blank=True, null=True, verbose_name="備考")),
            ],
        ),
        migrations.CreateModel(
            name="PaymentMethod",
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
                    "payee",
                    models.CharField(default="", max_length=64, verbose_name="支払先"),
                ),
                ("amounts", models.IntegerField(default=0, verbose_name="金額")),
                (
                    "banking_fee",
                    models.CharField(
                        blank=True, max_length=32, null=True, verbose_name="銀行手数料"
                    ),
                ),
                (
                    "account_description",
                    models.TextField(blank=True, null=True, verbose_name="摘要"),
                ),
                (
                    "comment",
                    models.CharField(
                        blank=True, max_length=64, null=True, verbose_name="備考"
                    ),
                ),
            ],
        ),
    ]
