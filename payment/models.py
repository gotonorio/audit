import datetime
import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from record.models import AccountingClass, Himoku

user = get_user_model()
logger = logging.getLogger(__name__)


class Payment(models.Model):
    """承認された支払いデータ
    費目コードはlimit_choices_toで勘定科目のフィルターをする。
    https://qiita.com/shimayu22/items/7d0f66da7c95508658e4
    https://docs.djangoproject.com/ja/4.2/ref/models/fields/#django.db.models.ForeignKey.limit_choices_to
    """

    payment_date = models.DateField(verbose_name="支払日", default=timezone.now)
    himoku = models.ForeignKey(Himoku, verbose_name="費目名", on_delete=models.CASCADE, null=True, blank=True)
    payment_destination = models.CharField(verbose_name="支払先", max_length=32, blank=True, default="")
    payment = models.IntegerField(verbose_name="金額", default=0)
    summary = models.CharField(verbose_name="摘要", max_length=64, blank=True, default="")

    def __str__(self):
        return self.summary

    @classmethod
    def payment_from_kurasel(cls, data):
        """クラセルの承認済み支払いデータを読み込む
        - 承認済みデータなので、金額の修正は無しとして「支払先、支払い金額、支払日, 摘要」でget_or_createする。
        - 費目はdefault費目をセットする。
        """
        # 支払日
        date_str = str(data["year"]) + str(data["month"]).zfill(2) + data["day"].zfill(2)
        payment_day = datetime.datetime.strptime(date_str, "%Y%m%d")
        error_list = []
        rtn = True
        # default費目を取得する。
        default_himoku = Himoku.get_default_himoku()
        for item in data["data_list"]:
            try:
                cls.objects.get_or_create(
                    payment_destination=item[2],
                    payment=item[3],
                    payment_date=payment_day,
                    # 2024-07-27「祭礼寄付」「盆踊り寄付」のため「摘要」を追加。
                    # したがって摘要を手入力すると、再読み込みすると同じデータを重複して取り込んでしまう。
                    summary=item[1],
                    defaults={
                        # "summary": item[1],
                        "himoku": default_himoku,
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
        qs = cls.objects.filter(payment_date__range=[tstart, tend])
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
    """入出金明細データ取り込み時に費目名を推定する為のマスタ（支払い方法と費目名の対応データ）
    - 支払い方法ごとに費目名を設定する。
    - 銀行手数料など特定の支払い方法に対して特定の費目名を設定するために使用する。
    """

    ac_class = models.ForeignKey(
        AccountingClass,
        verbose_name="会計区分",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    payment_category = models.ForeignKey(PaymentCategory, verbose_name="支払い区分", on_delete=models.CASCADE)
    himoku_name = models.ForeignKey(Himoku, verbose_name="費目名", on_delete=models.CASCADE)
    payee = models.CharField(verbose_name="支払先", max_length=64, default="")
    amounts = models.IntegerField(verbose_name="金額", default=0)
    banking_fee = models.CharField(verbose_name="銀行手数料", max_length=32, null=True, blank=True)
    account_description = models.TextField(verbose_name="摘要", null=True, blank=True)
    comment = models.CharField(verbose_name="備考", max_length=64, null=True, blank=True)

    def __str__(self):
        return self.payee

    @staticmethod
    def get_paymentmethod_obj():
        """支払い方法データ一覧をリストで返す"""
        qs = PaymentMethod.objects.all()
        obj_list = [obj for obj in qs]
        return obj_list
