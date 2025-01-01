import datetime
import logging

import jpholiday
from billing.models import Billing
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from kurasel_translator.my_lib.append_list import select_period
from kurasel_translator.my_lib.check_lib import check_period
from monthly_report.models import BalanceSheet, ReportTransaction
from passbook.forms import YearMonthForm
from payment.models import Payment
from record.models import ClaimData, Transaction

logger = logging.getLogger(__name__)


def get_lastmonth(year, month):
    """前月を返す"""
    # 当月1日の値を出す
    thismonth = datetime.datetime(int(year), int(month), 1)
    # 前月末日の値を出す
    lastmonth = thismonth + datetime.timedelta(days=-1)

    return lastmonth.year, lastmonth.month


class ApprovalExpenseCheckView(PermissionRequiredMixin, generic.TemplateView):
    """支払い承認データと入出金明細データの月別比較リスト
    - 入出金データの合計では、承認不要費目（資金移動、共用部電気料等）を除外する。
    - 未払金（貸借対照表データ）の表示。
    """

    template_name = "check_record/kurasel_ap_expense_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            year = kwargs.get("year")
            month = kwargs.get("month")
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)

        # 前月の年月
        lastyear, lastmonth = get_lastmonth(year, month)

        # Kuraselによる会計処理は2023年4月以降。それ以前は表示しない。
        year, month = check_period(year, month)

        # formの初期値を設定する。
        form = YearMonthForm(
            initial={
                "year": year,
                "month": month,
            }
        )
        # 当月の抽出期間
        tstart, tend = select_period(year, month)
        # 前月の抽出期間
        last_tstart, last_tend = select_period(lastyear, lastmonth)

        # ---------------------------------------------------------------------
        # 支払い承認データ
        # ---------------------------------------------------------------------
        qs_payment, total_ap = Payment.kurasel_get_payment(tstart, tend)
        # 入出金明細データの取得。（口座は常に""とする）
        qs_pb = Transaction.get_qs_pb(tstart, tend, "0", "0", "expense", False)
        qs_pb = qs_pb.order_by("transaction_date", "himoku__code")
        # step1 摘要欄コメントで支払い承認の有無をチェック。
        _ = Transaction.set_is_approval_text(qs_pb)
        # step2 費目で支払い承認の有無をチェック。
        _ = Transaction.set_is_approval_himoku(qs_pb)

        # 支出合計金額。（支払い承認が必要な費目だけの合計とする）
        total_pb = 0
        for d in qs_pb:
            if d.is_approval:
                total_pb += d.amount

        # ---------------------------------------------------------------------
        # 未払いデータ
        # ---------------------------------------------------------------------
        qs_this_miharai, total_miharai = BalanceSheet.get_miharai_bs(tstart, tend)

        # 前月の未払金
        qs_last_miharai = BalanceSheet.objects.filter(monthly_date__range=[last_tstart, last_tend]).filter(
            item_name__item_name__contains="未払金"
        )
        # 前月の未収金合計
        total_last_miharai = 0
        for d in qs_last_miharai:
            total_last_miharai += d.amounts

        context["mr_list"] = qs_payment
        context["pb_list"] = qs_pb
        context["total_mr"] = total_ap
        context["total_pb"] = total_pb
        context["total_diff"] = total_pb - total_ap
        context["form"] = form
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["this_miharai"] = qs_this_miharai
        context["this_miharai_total"] = total_miharai
        context["last_miharai"] = qs_last_miharai
        context["last_miharai_total"] = total_last_miharai
        context["year"] = year
        context["month"] = month

        return context


class MonthlyReportExpenseCheckView(PermissionRequiredMixin, generic.TemplateView):
    """月次収支の支出データと口座支出データの月別比較リスト"""

    template_name = "check_record/kurasel_mr_expense_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            year = kwargs.get("year")
            month = kwargs.get("month")
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)

        # 前月の年月
        lastyear, lastmonth = get_lastmonth(year, month)

        # Kuraselによる会計処理は2023年4月以降。それ以前は表示しない。
        year, month = check_period(year, month)

        # formの初期値を設定する。
        form = YearMonthForm(
            initial={
                "year": year,
                "month": month,
            }
        )
        # 当月の抽出期間
        tstart, tend = select_period(year, month)
        # 前月の抽出期間
        last_tstart, last_tend = select_period(lastyear, lastmonth)

        # ---------------------------------------------------------------------
        # 月次収支の支出データ
        # ---------------------------------------------------------------------
        qs_mr = ReportTransaction.get_monthly_report_expense(tstart, tend)
        # 月次収支の支出合計（ネッティング処理、集計フラグがFalseの費目を除外する）
        qs_mr_without_netting = qs_mr.exclude(is_netting=True).exclude(himoku__aggregate_flag=False)
        total_mr = ReportTransaction.calc_total_withflg(qs_mr_without_netting, True)

        # ---------------------------------------------------------------------
        # 入出金明細の支出データ
        # ---------------------------------------------------------------------
        qs_pb = Transaction.get_qs_pb(tstart, tend, "0", "0", "expense", True)
        qs_pb = qs_pb.order_by("transaction_date", "himoku__code", "description")
        # 通帳データの合計（集計フラグがTrueの費目合計）
        total_pb = 0
        for d in qs_pb:
            # 費目名が「不明」の場合も考慮する
            if d.himoku and d.himoku.aggregate_flag:
                total_pb += d.amount

        # ---------------------------------------------------------------------
        # 当月の未払い
        # ---------------------------------------------------------------------
        qs_this_miharai = (
            BalanceSheet.objects.filter(amounts__gt=0)
            .filter(monthly_date__range=[tstart, tend])
            .filter(item_name__item_name__contains="未払金")
        )
        # 当月の未払金合計
        total_miharai = 0
        for d in qs_this_miharai:
            total_miharai += d.amounts

        # 前月の未払金
        qs_last_miharai = (
            BalanceSheet.objects.filter(amounts__gt=0)
            .filter(monthly_date__range=[last_tstart, last_tend])
            .filter(item_name__item_name__contains="未払金")
        )
        # 前月の未払金合計
        total_last_miharai = 0
        for d in qs_last_miharai:
            total_last_miharai += d.amounts

        # 2023年4月（Kurasel監査の開始月）前月の未払金
        if int(year) == settings.START_KURASEL["year"] and int(month) == settings.START_KURASEL["month"]:
            total_last_miharai = settings.MIHARAI_INITIAL

        context["mr_list"] = qs_mr
        context["pb_list"] = qs_pb
        context["total_mr"] = total_mr
        context["total_pb"] = total_pb
        context["total_diff"] = total_pb - total_mr - total_last_miharai
        context["this_miharai"] = qs_this_miharai
        context["total_miharai"] = total_miharai
        context["last_miharai"] = qs_last_miharai
        context["last_miharai_total"] = total_last_miharai
        context["form"] = form
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["year"] = year
        context["month"] = month

        return context


class MonthlyReportIncomeCheckView(PermissionRequiredMixin, generic.TemplateView):
    """月次報告の収入データと口座収入データの月別比較リスト"""

    template_name = "check_record/kurasel_mr_income_check.html"
    permission_required = ("record.view_transaction",)

    def check_debit_date(self, debit_date):
        for i in range(0, 7):
            next_day = debit_date + datetime.timedelta(days=i)
            if not jpholiday.is_holiday(next_day) or next_day.weekday() < 5:
                return next_day

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            year = kwargs.get("year")
            month = kwargs.get("month")
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)

        # 前月の年月
        lastyear, lastmonth = get_lastmonth(year, month)

        # 追加contextデータの初期化
        context["netting_total"] = 0
        context["total_last_maeuke"] = 0
        context["total_mishuu_bs"] = 0
        context["total_mishuu_claim"] = 0
        context["total_last_mishuu"] = 0
        context["total_mr"] = 0
        context["total_pb"] = 0

        # Kuraselによる会計処理は2023年4月以降。
        year, month = check_period(year, month)

        # formの初期値を設定する。
        form = YearMonthForm(
            initial={
                "year": year,
                "month": month,
            }
        )

        # 当月の抽出期間
        tstart, tend = select_period(year, month)
        # 前月の抽出期間
        last_tstart, last_tend = select_period(lastyear, lastmonth)

        # ---------------------------------------------------------------------
        # (1) 月次収入データを抽出
        # ---------------------------------------------------------------------
        qs_mr = ReportTransaction.get_qs_mr(tstart, tend, "0", "income", True)
        # 収入のない費目は除く
        qs_mr = qs_mr.exclude(amount=0).order_by("himoku")
        # 月次収支の収入合計
        total_mr = ReportTransaction.calc_total_withflg(qs_mr, True)

        # ---------------------------------------------------------------------
        # (2) 入出金明細データ（通帳データ）の収入リスト
        # ---------------------------------------------------------------------
        qs_pb = Transaction.get_qs_pb(tstart, tend, "0", "0", "income", True)
        # 2023年3月以前のデータを除外する。
        start_date = datetime.date(2023, 4, 1)
        qs_pb = qs_pb.filter(transaction_date__gte=start_date)
        # 資金移動は除く
        qs_pb = qs_pb.filter(himoku__aggregate_flag=True).order_by("transaction_date", "himoku")
        # 収入合計金額
        total_pb, _ = Transaction.calc_total(qs_pb)

        # ---------------------------------------------------------------------
        # (3) 請求時点前受金リスト（当月使用する前受金）
        # ---------------------------------------------------------------------
        total_last_maeuke, qs_last_maeuke, total_comment = ClaimData.get_maeuke_claim(year, month)
        if settings.DEBUG:
            logger.debug(f"{month}月度の請求時前受金＝{total_last_maeuke:,}")

        # ---------------------------------------------------------------------
        # (4) 請求時点の未収金リストおよび未収金額
        # ---------------------------------------------------------------------
        total_mishuu_claim, qs_mishuu = ClaimData.get_mishuu(year, month)
        if settings.DEBUG:
            logger.debug(f"{month}月度の請求時未収金＝{total_mishuu_claim:,}")
        # 確認のため貸借対照表データから前月の未収金を計算する。
        last_mishuu_bs, total_last_mishuu = BalanceSheet.get_mishuu_bs(last_tstart, last_tend)
        if settings.DEBUG:
            logger.debug(f"{lastmonth}月度貸借対照表の未収金＝{total_last_mishuu:,}")
        check_last_mishuu = total_mishuu_claim - total_last_maeuke

        # ---------------------------------------------------------------------
        # (5) 貸借対照表データから当月の未収金を計算する。
        # ---------------------------------------------------------------------
        qs_mishuu_bs, total_mishuu_bs = BalanceSheet.get_mishuu_bs(tstart, tend)

        # ---------------------------------------------------------------------
        # (6) 自動控除された口座振替手数料。 自動控除費目の当月分金額を求める。
        #     aggregateで集約する場合は抽出結果がDictとなる
        # ---------------------------------------------------------------------
        qs_is_netting = ReportTransaction.objects.filter(transaction_date__range=[tstart, tend])
        qs_is_netting = qs_is_netting.filter(is_netting=True)
        qs_is_netting = qs_is_netting.aggregate(netting_total=Sum("amount"))
        netting_total = qs_is_netting["netting_total"]
        # 相殺項目合計が存在しない場合をチェック
        if netting_total is None:
            netting_total = 0
        # 2024年4月度の処理。Kurasel監査の開始月（2024年4月）前月の未収金は規定値とする。
        if year == settings.START_KURASEL["year"] and month == settings.START_KURASEL["month"]:
            total_last_mishuu = settings.MISHUU_KANRI + settings.MISHUU_SHUUZEN + settings.MISHUU_PARKING

        # 月次収入データ
        context["mr_list"] = qs_mr
        # 入出金明細データ
        context["pb_list"] = qs_pb
        # ネッティング額（相殺処理額）
        context["netting_total"] = netting_total
        # 貸借対照表上の未収金リストと未収金額
        context["mishuu_list"] = qs_mishuu_bs
        context["total_mishuu_bs"] = total_mishuu_bs
        # 貸借対照表上の前月未収金額
        context["last_mishuu_bs"] = last_mishuu_bs
        # 請求時点未収金一覧の合計
        context["total_mishuu_claim"] = total_mishuu_claim
        # 前月の貸借対照表データの未収金
        context["total_last_mishuu"] = total_last_mishuu
        # 使用する前受金の合計
        context["total_last_maeuke"] = -total_last_maeuke
        context["total_comment"] = total_comment
        # 月次収入データの合計
        context["total_mr"] = total_mr
        context["total_pb"] = total_pb + netting_total
        context["total_diff"] = context["total_pb"] - (total_mr - total_last_maeuke + total_mishuu_claim)
        # formデータ
        context["form"] = form
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["year"] = year
        context["month"] = month
        # 「前受金を考慮した月次報告の未収金額」と「前月の貸借対照表での未収金額」をチェックする
        context["check_last_mishuu"] = check_last_mishuu
        return context


class BillingAmountCheckView(PermissionRequiredMixin, generic.TemplateView):
    """請求金額内訳データと口座収入データの月別比較リスト"""

    template_name = "check_record/kurasel_ba_income_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            year = kwargs.get("year")
            month = kwargs.get("month")
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)

        # 当月の抽出期間
        tstart, tend = select_period(year, month)
        # forms.pyのKeikakuListFormに初期値を設定する
        form = YearMonthForm(
            initial={
                "year": year,
                "month": month,
            }
        )

        # ---------------------------------------------------------------------
        # (1) 請求金額内訳データを抽出
        # ---------------------------------------------------------------------
        qs_ba = Billing.get_billing_list(tstart, tend)
        # 表示順序
        qs_ba = qs_ba.order_by(
            "billing_item__code",
        )
        # 合計金額
        billing_total = Billing.calc_total_billing(qs_ba)

        # ---------------------------------------------------------------------
        # (2) 入出金明細データ（通帳データ）の収入リスト
        # ---------------------------------------------------------------------
        qs_pb = Transaction.get_qs_pb(tstart, tend, "0", "0", "income", True)
        # 2023年3月以前のデータを除外する。
        start_date = datetime.date(2023, 4, 1)
        qs_pb = qs_pb.filter(transaction_date__gte=start_date)
        # 資金移動は除く
        qs_pb = qs_pb.filter(himoku__aggregate_flag=True).order_by("transaction_date", "himoku")
        # 収入合計金額
        total_pb, _ = Transaction.calc_total(qs_pb.filter(is_billing=True))

        # ---------------------------------------------------------------------
        # (3) 自動控除された口座振替手数料。
        # ---------------------------------------------------------------------
        qs_is_netting = ReportTransaction.objects.filter(transaction_date__range=[tstart, tend])
        qs_is_netting = qs_is_netting.filter(is_netting=True)
        dict_is_netting = qs_is_netting.aggregate(netting_total=Sum("amount"))
        netting_total = dict_is_netting["netting_total"]
        # 相殺項目合計が存在しない場合をチェック
        if netting_total is None:
            netting_total = 0

        # ---------------------------------------------------------------------
        # (4) 当月の口座振替不備分を求める
        # ---------------------------------------------------------------------
        _, transfer_error = ClaimData.get_claim_list(tstart, tend, "振替不備")
        if settings.DEBUG:
            logger.debug(transfer_error)

        # 請求金額内訳データ
        context["billing_list"] = qs_ba
        context["billing_total"] = billing_total
        # 入出金明細データ
        context["pb_list"] = qs_pb
        # ネッティング額（相殺処理額）
        context["netting_total"] = netting_total
        # 入出金明細データの合計（前受金は月次報告で処理のため合計には加えない）
        context["total_pb"] = total_pb + netting_total
        context["form"] = form
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["year"] = year
        context["month"] = month
        # 請求金額と収入金額の差
        context["total_diff"] = total_pb + netting_total - billing_total
        # 当月の口座振替不備
        context["transfer_error"] = transfer_error
        return context


class YearReportIncomeCheckView(PermissionRequiredMixin, generic.TemplateView):
    """月次報告の年間収入データと口座収入データの比較リスト"""

    template_name = "check_record/year_income_check.html"
    permission_required = ("record.view_transaction",)

    def check_debit_date(self, debit_date):
        for i in range(0, 7):
            next_day = debit_date + datetime.timedelta(days=i)
            if not jpholiday.is_holiday(next_day) or next_day.weekday() < 5:
                return next_day

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            year = kwargs.get("year")
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)

        # 追加contextデータの初期化
        context["netting_total"] = 0
        context["total_mishuu_bs"] = 0
        context["total_mishuu_claim"] = 0
        context["total_last_mishuu"] = 0
        context["total_mr"] = 0
        context["total_pb"] = 0
        # 口座振替不備分
        context["transfer_error"] = 0

        # formの初期値を設定する。
        form = YearMonthForm(
            initial={
                "year": year,
                # "month": month,
            }
        )

        # 当月の抽出期間
        tstart, tend = select_period(year, 0)

        # ---------------------------------------------------------------------
        # (1) 月次収入データを抽出
        # ---------------------------------------------------------------------
        mr_year_income = ReportTransaction.get_year_income(tstart, tend, "0", True)
        # 収入のない費目は除く
        mr_year_income = mr_year_income.exclude(amount=0)
        # 年間収入の合計
        total_year_income = 0
        for i in mr_year_income:
            total_year_income += i["price"]

        # ---------------------------------------------------------------------
        # (2) 入出金明細データ（通帳データ）の収入リスト
        # ---------------------------------------------------------------------
        pb_year_income = Transaction.get_year_income(tstart, tend, "0", "0", True)
        # 2023年3月以前のデータを除外する。
        start_date = datetime.date(2023, 4, 1)
        pb_year_income = pb_year_income.filter(transaction_date__gte=start_date)
        # 資金移動は除く
        pb_year_income = pb_year_income.filter(himoku__aggregate_flag=True).order_by("himoku")
        # 収入合計金額
        total_pb = 0
        for i in pb_year_income:
            total_pb += i["price"]

        # ---------------------------------------------------------------------
        # (3) 貸借対照表データから当年12月の未収金を計算する。
        # ---------------------------------------------------------------------
        start_date, end_date = select_period(year, 12)
        qs_mishuu_bs, total_mishuu_bs = BalanceSheet.get_mishuu_bs(start_date, end_date)

        # ---------------------------------------------------------------------
        # (4) 自動控除された口座振替手数料。 自動控除費目の当月分金額を求める。
        # ---------------------------------------------------------------------
        qs_is_netting = ReportTransaction.objects.filter(transaction_date__range=[tstart, tend])
        qs_is_netting = qs_is_netting.filter(is_netting=True)
        dict_is_netting = qs_is_netting.aggregate(netting_total=Sum("amount"))
        netting_total = dict_is_netting["netting_total"]
        # 相殺項目合計が存在しない場合をチェック
        if netting_total is None:
            netting_total = 0

        # 月次収入データ
        context["year_list"] = mr_year_income
        # 入出金明細データ
        context["pb_list"] = pb_year_income
        # ネッティング額（相殺処理額）
        context["netting_total"] = netting_total
        # 貸借対照表上の未収金リストと未収金額
        context["mishuu_list"] = qs_mishuu_bs
        context["total_mishuu_bs"] = total_mishuu_bs
        # 月次収入データの合計
        context["total_mr"] = total_year_income
        # 入出金明細データの合計
        context["total_pb"] = total_pb + netting_total
        context["total_diff"] = context["total_pb"] - total_year_income
        context["form"] = form
        context["yyyymm"] = str(year) + "年"
        context["year"] = year
        return context
