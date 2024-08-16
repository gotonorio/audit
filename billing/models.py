from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

user = get_user_model()


class BillingItem(models.Model):
    """請求項目マスタデータ"""

    code = models.IntegerField(verbose_name="コード", unique=True)
    item_name = models.CharField(verbose_name="請求項目名", max_length=64)
    alive = models.BooleanField(verbose_name="有効", default=True)


class Billing(models.Model):
    """請求データ"""

    code = models.IntegerField(verbose_name="コード", unique=True)
    transaction_date = models.DateField("取引月")
    billing_item = models.ForeignKey(BillingItem, verbose_name="請求内訳名", on_delete=models.CASCADE)
    billing_ammount = models.IntegerField("請求金額", default=0)
    comment = models.CharField("備考", max_length=64, blank=True, default="")
    author = models.ForeignKey(user, verbose_name="記録者", on_delete=models.CASCADE, null=True)
    created_date = models.DateTimeField(verbose_name="作成日", default=timezone.now)

    def __str__(self):
        return self.billing_item
