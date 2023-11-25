import logging
import datetime

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.db.models.aggregates import Sum

from record.models import Himoku, AccountingClass

user = get_user_model()
logger = logging.getLogger(__name__)


class Payment(models.Model):
    """承認された支払いデータ
    費目コードはlimit_choices_toで勘定科目のフィルターをする。
    https://qiita.com/shimayu22/items/7d0f66da7c95508658e4
    https://docs.djangoproject.com/ja/4.2/ref/models/fields/#django.db.models.ForeignKey.limit_choices_to
    """

    payment_date = models.DateField(verbose_name="支払日", default=timezone.now)
    himoku = models.ForeignKey(
        Himoku, verbose_name="費目名", on_delete=models.CASCADE, null=True, blank=True
    )
    payment_destination = models.CharField(
        verbose_name="支払先", max_length=32, blank=True, default=""
    )
    payment = models.IntegerField(verbose_name="金額", default=0)
    summary = models.CharField(verbose_name="摘要", max_length=64, blank=True, default="")

    def __str__(self):
        return self.summary

    @classmethod
    def payment_from_kurasel(cls, data):
        """kurasel_translatorから承認済み支払いデータを読み込む。
        - 承認済みデータなので、金額の修正は無しとして「摘要、支払先、支払い金額、支払日」でget_or_createする。
        - 費目は取り敢えず「不明」に決め打ち（費目は手入力となる）
        """
        # 支払日
        date_str = str(data["year"]) + str(data["month"]) + data["day"]
        payment_day = datetime.datetime.strptime(date_str, "%Y%m%d")
        error_list = []
        rtn = True
        for item in data["data_list"]:
            try:
                cls.objects.update_or_create(
                    summary=item[1],
                    payment_destination=item[2],
                    payment_date=payment_day,
                    defaults={
                        "payment": int(item[3]),
                        "himoku": Himoku.get_himoku_obj(item[4], "all"),
                    },
                )
            except Exception as e:
                logger.error(e)
                error_list.append(item[0])
                rtn = False
        return rtn, error_list

    @classmethod
    def kurasel_get_payment(cls, tstart, tend):
        """承認済み支払いデータを返す"""
        qs = Payment.objects.filter(payment_date__range=[tstart, tend])
        total = 0
        for i in qs:
            total += i.payment
        return qs, total


class PaymentCategory(models.Model):
    """支払い区分マスタ"""

    payment_name = models.CharField(verbose_name="支払い種別名", max_length=32)
    comment = models.TextField(verbose_name="備考", null=True, blank=True)

    def __str__(self):
        return self.payment_name


class PaymentMethod(models.Model):
    """支払い方法"""

    ac_class = models.ForeignKey(
        AccountingClass,
        verbose_name="会計区分",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    payment_category = models.ForeignKey(
        PaymentCategory, verbose_name="支払い区分", on_delete=models.CASCADE
    )
    himoku_name = models.ForeignKey(
        Himoku, verbose_name="費目名", on_delete=models.CASCADE
    )
    payee = models.CharField(verbose_name="支払先", max_length=64, default="")
    amounts = models.IntegerField(verbose_name="金額", default=0)
    banking_fee = models.CharField(
        verbose_name="銀行手数料", max_length=32, null=True, blank=True
    )
    account_description = models.TextField(verbose_name="摘要", null=True, blank=True)
    comment = models.CharField(verbose_name="備考", max_length=64, null=True, blank=True)

    def __str__(self):
        return self.payee

    @staticmethod
    def get_paymentmethod_obj():
        qs = PaymentMethod.objects.all()
        obj_list = [obj for obj in qs]
        return obj_list
