import datetime
import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

user = get_user_model()
logger = logging.getLogger(__name__)


class BillingItem(models.Model):
    """請求項目マスタデータ
    - code: 請求項目コード
    - item_name: 請求項目名
    - is_billing: 請求合計金額に含めるかどうか（請求外入金は含めない）
    - alive: 有効かどうか
    - get_billingitem_obj: 請求合計金額内訳名からそのオブジェクトを返す
    - __str__: 請求項目名を返す
    """

    code = models.IntegerField(verbose_name="コード", unique=True)
    item_name = models.CharField(verbose_name="請求項目名", max_length=64)
    is_billing = models.BooleanField(default=True)
    alive = models.BooleanField(verbose_name="有効", default=True)

    def __str__(self):
        return self.item_name

    @classmethod
    def get_billingitem_obj(cls, item_name):
        """請求合計金額内訳名からそのオブジェクトを返す
        - 請求合計金額内訳名が存在しない場合はNoneを返す。
        """
        try:
            qs = cls.objects.get(
                alive=True,
                item_name=item_name,
            )
        except cls.DoesNotExist:
            qs = None
        return qs


class Billing(models.Model):
    """請求データ
    - transaction_date: 取引月
    - billing_item: 請求内訳名
    - billing_amount: 請求金額
    - comment: 備考
    - get_billing_data_qs: 請求合計金額内訳データの抽出を行う
    - billing_from_kurasel: Kuraselからの請求合計金額内訳データの保存処理を行う
    - calc_total_billing: 合計計算を行う
    """

    transaction_date = models.DateField("取引月")
    billing_item = models.ForeignKey(BillingItem, verbose_name="請求内訳名", on_delete=models.CASCADE)
    billing_amount = models.IntegerField("請求金額", default=0)
    comment = models.CharField("備考", max_length=64, blank=True, default="")
    author = models.ForeignKey(user, verbose_name="記録者", on_delete=models.CASCADE, null=True)
    created_date = models.DateTimeField(verbose_name="作成日", default=timezone.now)

    def __str__(self):
        return self.billing_item.item_name

    @classmethod
    def get_billing_data_qs(cls, tstart, tend):
        """請求合計金額内訳データの抽出を行う"""

        qs_billing = cls.objects.select_related("billing_item")
        qs_billing = qs_billing.filter(transaction_date__range=[tstart, tend])
        return qs_billing

    @staticmethod
    def calc_total_billing(sql):
        """合計計算"""
        total_billing = 0
        for data in sql:
            if data.billing_item.is_billing:
                total_billing += data.billing_amount
        return total_billing

    @classmethod
    def billing_from_kurasel(cls, data):
        """請求合計金額内訳データの保存処理を行う"""

        # 取引月
        date_str = str(data["year"]) + "-" + str(data["month"]) + "-" + "01"
        ymd = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        # 記録者
        author_obj = user.objects.get(id=data["author"])
        # error flag
        error_list = []
        rtn = True
        for item in data["data_list"]:
            # Kuraselの費目名と一致する費目オブジェクトを得る
            billingitem_id = BillingItem.get_billingitem_obj(item[0])
            if billingitem_id is None:
                return False, [
                    "請求合計金額内訳名「" + item[0] + "」がマスタデータに登録されていません。",
                ]
            try:
                cls.objects.update_or_create(
                    transaction_date=ymd,
                    billing_item=billingitem_id,
                    defaults={
                        "billing_amount": int(item[1]),
                        "comment": "",
                        "author": author_obj,
                    },
                )
            except Exception as e:
                logger.error(e)
                error_list.append(item[0])
                rtn = False
        return rtn, error_list
