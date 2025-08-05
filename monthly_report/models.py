import calendar
import datetime
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.db.models.aggregates import Sum
from django.utils import timezone

from record.models import Account, AccountingClass, Himoku

user = get_user_model()
logger = logging.getLogger(__name__)


class ReportTransaction(models.Model):
    """月次収支データモデル"""

    account = models.ForeignKey(
        Account, verbose_name="口座名", on_delete=models.CASCADE, null=True
    )
    accounting_class = models.ForeignKey(
        AccountingClass,
        verbose_name="会計区分",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    transaction_date = models.DateField("取引月")
    amount = models.IntegerField("金額", default=0)
    himoku = models.ForeignKey(
        Himoku, verbose_name="費目名", on_delete=models.CASCADE, null=True
    )
    calc_flg = models.BooleanField(verbose_name="計算対象", default=True)
    description = models.CharField("摘要", max_length=64, blank=True, default="")
    author = models.ForeignKey(
        user, verbose_name="記録者", on_delete=models.CASCADE, null=True
    )
    created_date = models.DateTimeField(verbose_name="作成日", default=timezone.now)
    delete_flg = models.BooleanField(default=False)
    is_netting = models.BooleanField(verbose_name="相殺処理", default=False)
    is_miharai = models.BooleanField(verbose_name="未払い", default=False)
    is_manualinput = models.BooleanField(default=False)

    def __str__(self):
        return self.himoku.himoku_name

    # def delete(self):
    #     """ delete関数を論理削除にするためにオーバーライド
    #     - DeleteViewで削除処理すると、レコードは削除せずdelete_flgをTrueにする。
    #     """
    #     self.delete_flg = True
    #     self.save()

    @classmethod
    def get_qs_mr(cls, tstart, tend, ac_class, inout_flg, community):
        """指定された「年月」「会計区分」「入金・支出」「町内会会計」で抽出する月次報告querysetを返す。
        - 資金移動は含むので、必要なら呼び出し側で処理する。
        - ac_class == "0"の場合、全会計区分を対象とする。
        - flg==''の場合は入出金データを抽出する。
        - communityフラグがFalseの場合、町内会会計を除いて抽出する。 2024-1-25に追加
        - 費目コードが9000以上は使用しないため表示しないようにする。有効フラグをOFFにすると、（Kuraselからの取り込みチェックでアウト）
        """
        qs_mr = cls.objects.all().select_related("himoku", "accounting_class")
        # (1) 期間でfiler
        qs_mr = qs_mr.filter(transaction_date__range=[tstart, tend])
        # (2) 削除フラグをチェック
        qs_mr = qs_mr.filter(delete_flg=False)
        # (3) 収入・支出でfilter
        if inout_flg == "income":
            qs_mr = qs_mr.filter(himoku__is_income=True)
        elif inout_flg == "expense":
            qs_mr = qs_mr.filter(himoku__is_income=False)
        # (4) 有効な費目、支出のある費目でfilter
        qs_mr = qs_mr.filter(himoku__alive=True).exclude(amount=0)
        # (5) 費目の会計区分でfilter 2023-11-23に追加
        if ac_class != "0":
            qs_mr = qs_mr.filter(himoku__accounting_class=ac_class)
        # (6) 町内会会計を除くかどうか
        if not community:
            obj = AccountingClass.get_accountingclass_obj(
                AccountingClass.get_class_name("町内会")
            )
            qs_mr = qs_mr.exclude(himoku__accounting_class=obj.pk)
        return qs_mr

    @staticmethod
    def total_calc_flg(sql, community=True):
        """計算対象の合計計算
        - community = False：町内会費目を除外する
        - aggregate_flag = Falseの費目は集計しない。
        """
        if not community:
            obj = AccountingClass.get_accountingclass_obj(
                AccountingClass.get_class_name("町内会")
            )
            sql = sql.exclude(himoku__accounting_class=obj.pk)
        # 計算対象でフィルター
        sql = sql.filter(himoku__aggregate_flag=True)

        total_withdrawals = 0
        for data in sql:
            if data.calc_flg:
                total_withdrawals += data.amount

        return total_withdrawals

    @staticmethod
    def calc_total_withflg(sql, flg):
        """合計計算
        flg = Trueの場合、計算対象(calc_flg=True)の費目データだけ合計する。
        flg = Falseの場合、全てのデータを合計する。
        2024-02-15 上記に関わらず、費目のaggregate_flagがFalseの場合は集計しない。
        """
        total_withdrawals = 0
        if flg:
            for data in sql:
                # if data.himoku.aggregate_flag:
                if data.calc_flg and data.himoku.aggregate_flag:
                    total_withdrawals += data.amount
        else:
            for data in sql:
                total_withdrawals += data.amount
        return total_withdrawals

    # @classmethod
    # def get_monthly_report_expense(cls, tstart, tend, community=False):
    #     """資金移動を除いて、計算対象の支出データを抽出するsqlを返す"""
    #     # 月次報告データの取得（Kurasel監査の月次報告支出チェックでは町内会会計を除外する）
    #     qs_mr = cls.get_qs_mr(tstart, tend, "0", "expense", community)
    #     return qs_mr

    # @classmethod
    # def get_monthly_report_income(cls, tstart, tend):
    #     """月次報告の収入データのquerysetを返す"""

    #     # 月次報告データの取得（Kurase監査の月次報告収入チェックでは町内会会計も含める）
    #     qs_mr = cls.get_qs_mr(tstart, tend, "0", "income", True)
    #     # # 資金移動は除く
    #     # qs_mr = qs_mr.filter(himoku__aggregate_flag=True)
    #     # 通帳データと比較のため、calc_flgがFalseを除く。表示だけはすることにした。
    #     # qs_mr = qs_mr.filter(calc_flg=True)
    #     return qs_mr

    @classmethod
    def monthly_from_kurasel(cls, ac_class, data):
        """月次収支データの保存処理を行う
        - 会計区分を指定して取り込む。
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
            # Kuraselの費目名と一致する費目オブジェクトを得る
            himoku_id = Himoku.get_himoku_obj(item[0], ac_class)
            if himoku_id is None:
                return False, [
                    "費目名「" + item[0] + "」が費目リストに登録されていません。",
                ]
            try:
                ac_class_obj = AccountingClass.get_accountingclass_obj(ac_class)
                cls.objects.update_or_create(
                    transaction_date=ymd,
                    himoku=himoku_id,
                    accounting_class=ac_class_obj,
                    defaults={
                        # 口座は1つだけなので、first()で取得できる。
                        "account": Account.objects.all().first(),
                        "amount": int(item[2]),
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
    def set_offset_flag(cls, himoku, tstart, tend):
        """設定された費目名のレコードにis_nettingをセットする"""
        # 指定された年月の月次収支データで処理を行う。
        qs = cls.objects.filter(transaction_date__range=[tstart, tend])
        for data in qs:
            if data.himoku and data.himoku.himoku_name == himoku:
                update_obj = cls.objects.get(pk=data.pk)
                update_obj.is_netting = True
                update_obj.save()
        return True

    @classmethod
    def get_unpaid_balance(cls, start, end):
        """未払金リストを返す"""
        qs = (
            cls.objects.all()
            .filter(transaction_date__range=[start, end])
            .filter(is_miharai=True)
            .order_by("-transaction_date", "accounting_class")
        )
        return qs

    @classmethod
    def get_calcflg_check(cls, start, end):
        """合計計算対象外リスト
        - calc_flg = False
        - aggregate_flag = False
        """
        qs = (
            cls.objects.all()
            .filter(transaction_date__range=[start, end])
            .filter(Q(calc_flg=False) | Q(himoku__aggregate_flag=False))
            .filter(amount__gt=0)
            .order_by("accounting_class", "himoku", "transaction_date")
        )
        return qs

    @classmethod
    def get_year_income(cls, tstart, tend, community):
        """月次報告の年間収入リストを返す
        - 資金移動は含むので、必要なら呼び出し側で処理する。
        - communityフラグがFalseの場合、町内会会計を除いて抽出する。 2024-1-25に追加
        - 費目コードが9000以上は使用しないため表示しないようにする。有効フラグをOFFにすると、（Kuraselからの取り込みチェックでアウト）
        """
        # 費目で集約する
        qs_year_income = (
            cls.objects.select_related("himoku")
            .values("himoku__himoku_name")
            .annotate(price=Sum("amount"))
        )
        # (1) 期間でfiler
        qs_year_income = qs_year_income.filter(transaction_date__range=[tstart, tend])
        # (2) 削除フラグをチェック
        qs_year_income = qs_year_income.filter(delete_flg=False)
        # (3) 収入でfilter
        qs_year_income = qs_year_income.filter(himoku__is_income=True)
        # (4) 有効な費目、支出のある費目でfilter
        qs_year_income = qs_year_income.filter(himoku__alive=True).exclude(amount=0)
        # (6) 町内会会計を除くかどうか
        if community is False:
            obj = AccountingClass.get_accountingclass_obj(
                AccountingClass.get_class_name("町内会")
            )
            qs_year_income = qs_year_income.exclude(himoku__accounting_class=obj.pk)

        return qs_year_income.order_by("himoku")

    @classmethod
    def get_year_expense(cls, tstart, tend):
        """指定された「年月」「入金」」で抽出する月次報告をDictで返す。
        - 資金移動は含むので、必要なら呼び出し側で処理する。
        - 費目コードが9000以上（新規に使用禁止の費目）も過去に使用している場合を考慮して抽出する。
        """
        # 費目で集約する
        qs_year_expense = (
            cls.objects.select_related("himoku")
            .values("himoku__himoku_name", "himoku__aggregate_flag", "calc_flg")
            .annotate(price=Sum("amount"))
        )
        # (1) 期間でfiler
        qs_year_expense = qs_year_expense.filter(transaction_date__range=[tstart, tend])
        # (2) 収入でfilter
        qs_year_expense = qs_year_expense.filter(himoku__is_income=False)
        # (3) 有効で支出のある費目でfilter
        qs_year_expense = qs_year_expense.filter(himoku__alive=True).exclude(amount=0)
        # (4) 削除フラグをチェック
        qs_year_expense = qs_year_expense.filter(delete_flg=False)

        return qs_year_expense.order_by("himoku")


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
    """貸借対照表(Kurasel)の未収金、前受金保存モデル"""

    monthly_date = models.DateField(verbose_name="月度", null=True, blank=True)
    amounts = models.IntegerField(verbose_name="金額", default=0)
    item_name = models.ForeignKey(
        BalanceSheetItem, on_delete=models.CASCADE, null=True, blank=True
    )
    comment = models.CharField(
        verbose_name="備考", max_length=64, null=True, blank=True
    )

    def __int__(self):
        return self.amounts

    def __str__(self):
        return self.item_name.item_name

    @classmethod
    def get_bs(cls, tstart, tend, ac_class, is_asset):
        """期間と資産・負債フラグで貸借対照表データ抽出する。"""
        qs_bs = (
            cls.objects.all()
            .select_related("item_name")
            .filter(item_name__is_asset=is_asset)
        )
        # 期間でfiler
        qs_bs = qs_bs.filter(monthly_date__range=[tstart, tend])
        if ac_class:
            qs_bs = qs_bs.filter(item_name__ac_class=ac_class)
        else:
            qs_bs = qs_bs.values("item_name__item_name").annotate(
                all_amounts=Sum("amounts")
            )

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
            try:
                item_name_obj = BalanceSheetItem.objects.filter(ac_class=ac_class).get(
                    item_name=item_name
                )
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

    @classmethod
    def get_mishuu_bs(cls, tstart, tend):
        """指定期間の貸借対照表の未収金を返す"""
        qs_mishuu_bs = (
            cls.objects.filter(monthly_date__range=[tstart, tend])
            .filter(item_name__item_name__contains=settings.RECIVABLE)
            .order_by("item_name")
        )
        # 貸借対照表上の前月の未収金合計
        total_mishuu = 0
        for d in qs_mishuu_bs:
            total_mishuu += d.amounts

        return qs_mishuu_bs, total_mishuu

    @classmethod
    def get_miharai_bs(cls, tstart, tend):
        """期間の貸借対照表の未払金を返す"""
        qs_miharai = BalanceSheet.objects.filter(
            monthly_date__range=[tstart, tend]
        ).filter(item_name__item_name__contains=settings.PAYABLE)
        # 未払金合計
        total_miharai = 0
        for d in qs_miharai:
            total_miharai += d.amounts

        return qs_miharai, total_miharai

    @classmethod
    def get_maeuke_bs(cls, tstart, tend):
        """指定期間の貸借対照表の前受金を返す"""
        qs_maeuke_bs = (
            cls.objects.filter(monthly_date__range=[tstart, tend])
            .filter(item_name__item_name__contains=settings.MAEUKE)
            .order_by("item_name")
        )
        # 貸借対照表上の前月の未収金合計
        total_maeuke = 0
        for d in qs_maeuke_bs:
            total_maeuke += d.amounts

        return total_maeuke
