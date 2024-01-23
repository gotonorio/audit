import calendar
import datetime
import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.aggregates import Sum
from django.utils import timezone

from kurasel_translator.my_lib.append_list import select_period
from record.models import Account, AccountingClass, Himoku

user = get_user_model()
logger = logging.getLogger(__name__)


class ReportTransaction(models.Model):
    """月次報告書取引明細"""

    account = models.ForeignKey(Account, verbose_name="口座名", on_delete=models.CASCADE, null=True)
    accounting_class = models.ForeignKey(
        AccountingClass,
        verbose_name="会計区分",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    transaction_date = models.DateField("取引月")
    ammount = models.IntegerField("金額", default=0)
    himoku = models.ForeignKey(Himoku, verbose_name="費目名", on_delete=models.CASCADE, null=True)
    miharai_flg = models.BooleanField(default=False)
    mishuu_flg = models.BooleanField(default=False)
    calc_flg = models.BooleanField(verbose_name="計算対象", default=True)
    description = models.CharField("摘要", max_length=64, blank=True, default="")
    author = models.ForeignKey(user, verbose_name="記録者", on_delete=models.CASCADE, null=True)
    created_date = models.DateTimeField(verbose_name="作成日", default=timezone.now)
    delete_flg = models.BooleanField(default=False)
    is_netting = models.BooleanField(verbose_name="相殺処理", default=False)

    def __str__(self):
        return self.himoku.himoku_name

    # def delete(self):
    #     """ delete関数を論理削除にするためにオーバーライド
    #     - DeleteViewで削除処理すると、レコードは削除せずdelete_flgをTrueにする。
    #     """
    #     self.delete_flg = True
    #     self.save()

    # 振込手数料は同じ口座、費目、金額があるため、重複制限をなくす。
    # class Meta:
    #     """ https://djangobrothers.com/blogs/django_uniqueconstraint/ """
    #     constraints = [
    #         # 同じ月に同じ口座、費目、金額を重複させない
    #         models.UniqueConstraint(
    #             fields=['transaction_date', 'account', 'ammount', 'himoku'],
    #             name='unique_himoku'),
    #     ]

    @classmethod
    def get_qs_mr(cls, tstart, tend, himoku, account, ac_class, flg):
        """指定された「年月」「費目」「口座」「会計区分」「入金・支出」で抽出するquerysetを返す。
        - 資金移動は含むので、必要なら呼び出し側で処理する。
        - flg==''の場合は入出金データを抽出する。
        - himokuが「未収入金」の場合、mishuu_flgで抽出する。
        """
        qs_mr = cls.objects.all().select_related("himoku", "account")
        # (1) 期間でfiler
        qs_mr = qs_mr.filter(transaction_date__range=[tstart, tend])
        # (2) 削除フラグをチェック
        qs_mr = qs_mr.filter(delete_flg=False)
        # (3) 収入・支出でfilter
        if flg == "income":
            # 収入をfilter。
            qs_mr = qs_mr.filter(himoku__is_income=True)
        elif flg == "expense":
            # 支出をfilter。
            qs_mr = qs_mr.filter(himoku__is_income=False)
        # (4) 口座種類でfilter　ToDo Kuraseの場合不要となる予定
        if account != "":
            qs_mr = qs_mr.filter(account=account)
        # (5) 有効な費目でfilter
        qs_mr = qs_mr.filter(himoku__alive=True)
        # (6) 費目の会計区分でfilter 2023-11-23に追加
        if ac_class != "":
            qs_mr = qs_mr.filter(himoku__accounting_class=ac_class)
        return qs_mr

    #
    # for Kurasel
    #
    @staticmethod
    def calc_total_withflg(sql, flg):
        """合計計算
        flg = Trueの場合、計算対象のデータだけ合計する。
        flg = Falseの場合、全てのデータを合計する。
        """
        total_withdrawals = 0
        if flg:
            for data in sql:
                if data.calc_flg:
                    total_withdrawals += data.ammount
        else:
            for data in sql:
                total_withdrawals += data.ammount
        return total_withdrawals

    @classmethod
    def get_monthly_report_expense(cls, tstart, tend):
        """資金移動を除いて、計算対象データを抽出するsqlを返す"""
        # 月次報告データの取得
        qs_mr = cls.get_qs_mr(tstart, tend, "", "", "", "expense")
        # 資金移動は除く
        qs_mr = qs_mr.filter(himoku__aggregate_flag=True)
        # 未払金を取得。
        qs_miharai = qs_mr.filter(miharai_flg=True)
        # 計算対象データだけを抽出。
        qs_mr = qs_mr.filter(calc_flg=True)
        return qs_mr, qs_miharai

    @classmethod
    def get_monthly_report_income(cls, tstart, tend):
        """未収入金を分けて返す"""
        # 月次報告データの取得
        qs_mr = cls.get_qs_mr(tstart, tend, "", "", "", "income")
        # 資金移動は除く
        qs_mr = qs_mr.filter(himoku__aggregate_flag=True)
        # 通帳データと比較のため、calc_flgがFalseを除く。表示だけはすることにした。
        # qs_mr = qs_mr.filter(calc_flg=True)
        # 未収入金だけを取得。
        qs_mishuu = qs_mr.filter(mishuu_flg=True)
        # 未収入金を除くデータを取得。
        qs_mr = qs_mr.filter(mishuu_flg=False)
        return qs_mr, qs_mishuu

    @classmethod
    def monthly_from_kurasel(cls, ac_class, data):
        """kurasel_translatorから月次収支データを読み込む
        - 会計区分を指定して取り込む。ToDo:町内会会計の扱いを検討する。
        """
        # 取引月
        date_str = str(data["year"]) + "-" + str(data["month"]) + "-" + "01"
        ymd = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        # 記録者
        author_obj = user.objects.get(id=data["author"])
        # error flag
        error_list = []
        rtn = True
        for item in data["data_list"]:
            try:
                # himoku_id = Himoku.get_himoku_obj(item[0], ac_class)
                # ToDo allにすると、管理会計の「受取利息」修繕会計の「受取利息」があるため、修繕会計の「受取利息」を「無効」にしている。
                # Kuraselで修繕会計の「受取利息」を削除した場合に、費目マスタから削除する予定。
                himoku_id = Himoku.get_himoku_obj(item[0], ac_class)
                ac_class_obj = AccountingClass.get_accountingclass_obj(ac_class)
                cls.objects.update_or_create(
                    transaction_date=ymd,
                    himoku=himoku_id,
                    accounting_class=ac_class_obj,
                    defaults={
                        # 口座は1つだけなので、first()で取得できる。
                        "account": Account.objects.all().first(),
                        "ammount": int(item[2]),
                        "calc_flg": True,
                        "author": author_obj,
                    },
                )
            except Exception as e:
                logger.error(e)
                error_list.append(item[0])
                rtn = False
        return rtn, error_list

    @classmethod
    def set_offset_flag(cls, himoku, year, month):
        """設定された費目名のレコードにis_nettingをセットする"""
        # 指定された年月の月次収支データで処理を行う。
        tstart, tend = select_period(str(year), str(month))
        qs = cls.objects.filter(transaction_date__range=[tstart, tend])
        for data in qs:
            if data.himoku and data.himoku.himoku_name == himoku:
                update_obj = cls.objects.get(pk=data.pk)
                update_obj.is_netting = True
                update_obj.save()
        return True


class BalanceSheetItem(models.Model):
    """貸借対照表の項目
    - 管理会計 未収金/前受金/前払金/未払金
    - 修繕会計 未収金/前受金/前払金/未払金
    - 駐車場会計 未収金/前受金/前払金/未払金
    - 町内会会計 未収金/前受金/前払金/未払金
    """

    code = models.IntegerField(default=0)
    ac_class = models.ForeignKey(
        AccountingClass,
        verbose_name="会計区分",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    item_name = models.CharField(verbose_name="項目名", max_length=32)
    is_asset = models.BooleanField(verbose_name="資産項目", default=True)

    def __str__(self):
        return self.item_name


class BalanceSheet(models.Model):
    """貸借対照表の未収金、前受金保存モデル"""

    monthly_date = models.DateField(verbose_name="月度", null=True, blank=True)
    amounts = models.IntegerField(verbose_name="金額", default=0)
    item_name = models.ForeignKey(BalanceSheetItem, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.CharField(verbose_name="備考", max_length=64, null=True, blank=True)

    def __int__(self):
        return self.ammounts

    def __str__(self):
        return self.item_name.item_name

    @classmethod
    def get_bs(cls, tstart, tend, ac_class, is_asset):
        """期間と資産・負債フラグで貸借対照表データ抽出する。"""
        qs_bs = cls.objects.all().select_related("item_name").filter(item_name__is_asset=is_asset)
        # 期間でfiler
        qs_bs = qs_bs.filter(monthly_date__range=[tstart, tend])
        if ac_class:
            qs_bs = qs_bs.filter(item_name__ac_class=ac_class)
        else:
            qs_bs = qs_bs.values("item_name__item_name").annotate(all_amounts=Sum("amounts"))

        return qs_bs

    @classmethod
    def bs_from_kurasel(cls, ac_class, data):
        """kuraselから貸借対照表データを取り込む
        - 日付、項目名でupdate_or_createする
        """
        # 月度 日付は末日とする。
        last_day = calendar.monthrange(int(data["year"]), int(data["month"]))[1]
        date_str = str(data["year"]) + "-" + str(data["month"]) + "-" + str(last_day)
        monthly_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        error_list = []
        rtn = True
        for item_name, amounts in data["bs_dict"].items():
            # item_name_obj = BalanceSheetItem.objects.filter(ac_class=ac_class).get(item_name=item_name)
            try:
                item_name_obj = BalanceSheetItem.objects.filter(ac_class=ac_class).get(item_name=item_name)
                cls.objects.update_or_create(
                    monthly_date=monthly_date,
                    item_name=item_name_obj,
                    defaults={
                        "amounts": amounts,
                    },
                )
            except Exception as e:
                logger.error(e)
                error_list.append(item_name)
                rtn = False
        return rtn, error_list
