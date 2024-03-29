# Generated by Django 5.0.3 on 2024-03-18 04:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('record', '0005_approvalcheckdata'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClaimData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('claim_date', models.DateField(verbose_name='取引日')),
                ('claim_type', models.CharField(choices=[('未収金', '未収金'), ('前受金', '前受金')], default='未収金', max_length=4, verbose_name='請求種別')),
                ('room_no', models.CharField(default='', max_length=16, verbose_name='部屋番号')),
                ('name', models.CharField(default='', max_length=16, verbose_name='氏名')),
                ('ammount', models.IntegerField(default=0, verbose_name='金額')),
            ],
        ),
    ]
