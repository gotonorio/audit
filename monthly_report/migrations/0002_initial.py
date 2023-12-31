# Generated by Django 4.2.7 on 2023-11-25 11:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("record", "0001_initial"),
        ("monthly_report", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="reporttransaction",
            name="account",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="record.account",
                verbose_name="口座名",
            ),
        ),
        migrations.AddField(
            model_name="reporttransaction",
            name="accounting_class",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="record.accountingclass",
                verbose_name="会計区分",
            ),
        ),
    ]
