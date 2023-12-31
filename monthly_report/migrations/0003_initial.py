# Generated by Django 4.2.7 on 2023-11-25 11:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("monthly_report", "0002_initial"),
        ("record", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="reporttransaction",
            name="author",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name="記録者",
            ),
        ),
        migrations.AddField(
            model_name="reporttransaction",
            name="himoku",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="record.himoku",
                verbose_name="費目名",
            ),
        ),
        migrations.AddField(
            model_name="balancesheetitem",
            name="ac_class",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="record.accountingclass",
                verbose_name="会計区分",
            ),
        ),
        migrations.AddField(
            model_name="balancesheet",
            name="item_name",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="monthly_report.balancesheetitem",
            ),
        ),
    ]
