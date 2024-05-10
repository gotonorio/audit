import datetime
import logging

import jpholiday
from check_record.forms import KuraselCheckForm
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from kurasel_translator.my_lib.append_list import select_period
from kurasel_translator.my_lib.check_lib import check_period

# from check_record.views.views import get_lastmonth
from monthly_report.models import BalanceSheet, ReportTransaction
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

        # Kuraselによる会計処理は2023年4月以降。それ以前は表示しない。
        year, month = check_period(year, month)

        # formの初期値を設定する。
        form = KuraselCheckForm(
            initial={
                "year": year,
                "month": month,
            }
        )
        # ALL(全月)は処理しない
        if str(month).upper() == "ALL":
            context["warning_kurasel"] = "ALL(全月)の表示は無効です。"
            context["form"] = form
            return context

        # 抽出期間
        tstart, tend = select_period(year, month)
        # 支払い承認データ
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
                total_pb += d.ammount

        # 未払いデータ
        qs_this_miharai = BalanceSheet.objects.filter(monthly_date__range=[tstart, tend]).filter(
            item_name__item_name__contains="未払金"
        )
        # 未払金合計
        total_miharai = 0
        for d in qs_this_miharai:
            total_miharai += d.amounts

        # 前月の期間を計算。
        lastyear, lastmonth = get_lastmonth(year, month)
        last_tstart, last_tend = select_period(lastyear, lastmonth)
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

        # Kuraselによる会計処理は2023年4月以降。それ以前は表示しない。
        year, month = check_period(year, month)

        # formの初期値を設定する。
        form = KuraselCheckForm(
            initial={
                "year": year,
                "month": month,
            }
        )
        # ALL(全月)は処理しない
        if str(month).upper() == "ALL":
            context["warning_kurasel"] = "ALL(全月)の表示は無効です。"
            context["form"] = form
            return context

        # 抽出期間
        tstart, tend = select_period(year, month)
        # 月次収支の支出データ
        qs_mr = ReportTransaction.get_monthly_report_expense(tstart, tend)
        # 支出のない費目は除く
        qs_mr = qs_mr.filter(ammount__gt=0)
        # 月次収支の支出合計（ネッティング処理、集計フラグがFalseの費目を除外する）
        qs_mr_without_netting = qs_mr.exclude(is_netting=True).exclude(himoku__aggregate_flag=False)
        total_mr = ReportTransaction.calc_total_withflg(qs_mr_without_netting, True)
        # 入出金明細の支出データ
        qs_pb = Transaction.get_qs_pb(tstart, tend, "0", "0", "expense", True)
        qs_pb = qs_pb.order_by("transaction_date", "himoku__code", "description")
        # 通帳データの合計（集計フラグがTrueの費目合計）
        total_pb = 0
        for d in qs_pb:
            # 費目名が「不明」の場合も考慮する
            if d.himoku and d.himoku.aggregate_flag:
                total_pb += d.ammount

        # 当月の未払い
        qs_this_miharai = (
            BalanceSheet.objects.filter(amounts__gt=0)
            .filter(monthly_date__range=[tstart, tend])
            .filter(item_name__item_name__contains="未払金")
        )
        # 当月の未払金合計
        total_miharai = 0
        for d in qs_this_miharai:
            total_miharai += d.amounts

        # 前月の期間を計算。
        lastyear, lastmonth = get_lastmonth(year, month)
        last_tstart, last_tend = select_period(lastyear, lastmonth)
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

        # 追加contextデータの初期化
        context["netting_total"] = 0
        context["pb_last_maeuke"] = 0
        context["total_last_maeuke"] = 0
        context["total_mishuu_bs"] = 0
        context["total_last_mishuu"] = 0
        context["total_mr"] = 0
        context["total_pb"] = 0

        # Kuraselによる会計処理は2023年4月以降。
        year, month = check_period(year, month)

        # formの初期値を設定する。
        form = KuraselCheckForm(
            initial={
                "year": year,
                "month": month,
            }
        )

        # ALL(全月)は処理しない
        if str(month).upper() == "ALL":
            context["warning_kurasel"] = "ALL(全月)の表示は無効です。"
            context["form"] = form
            return context

        # 抽出期間
        tstart, tend = select_period(year, month)
        #
        # (1) 月次収入データを抽出
        #
        # qs_mr = ReportTransaction.get_monthly_report_income(tstart, tend)
        qs_mr = ReportTransaction.get_qs_mr(tstart, tend, "0", "income", True)
        # 収入のない費目は除く
        qs_mr = qs_mr.exclude(ammount=0)

        # 月次収支の収入合計
        total_mr = ReportTransaction.calc_total_withflg(qs_mr, True)

        #
        # (2) 入出金明細データ（通帳データ）の収入リスト
        #
        qs_pb = Transaction.get_qs_pb(tstart, tend, "0", "0", "income", True)
        # 2023年3月以前のデータを除外する。
        start_date = datetime.date(2023, 4, 1)
        qs_pb = qs_pb.filter(transaction_date__gte=start_date)
        # 資金移動は除く
        qs_pb = qs_pb.filter(himoku__aggregate_flag=True).order_by("transaction_date", "himoku")
        # 収入合計金額
        total_pb, _ = Transaction.calc_total(qs_pb)
        #
        # (3) 請求時点前受金リスト（当月使用する前受金）
        #
        total_last_maeuke, qs_last_maeuke, total_comment = ClaimData.get_maeuke(year, month)
        if settings.DEBUG:
            logger.debug(f"{month}月度の請求時前受金＝{total_last_maeuke:,}")
            # for i in qs_last_maeuke:
            #     logger.debug(i)

        #
        # (4) 請求時点未収金リスト->貸借対照表上の前月未収金のはずだが違う？
        #
        total_mishuu, qs_mishuu = ClaimData.get_mishuu(year, month)
        if settings.DEBUG:
            logger.debug(f"{month}月度の請求時未収金＝{total_mishuu:,}")
            # for i in qs_mishuu:
            #     logger.debug(i)

        # 自動控除された口座振替手数料。 自動控除費目の当月分金額を求める。
        qs_is_netting = ReportTransaction.objects.filter(transaction_date__range=[tstart, tend])
        qs_is_netting = qs_is_netting.filter(is_netting=True)
        # qs_is_netting = qs_is_netting.aggregate(commission_fee=Sum('ammount'))
        dict_is_netting = qs_is_netting.aggregate(netting_total=Sum("ammount"))
        netting_total = dict_is_netting["netting_total"]
        # 相殺項目合計が存在しない場合をチェック
        if netting_total is None:
            netting_total = 0

        # 貸借対照表データから当月の未収金を求める。
        qs_mishuu_bs = (
            BalanceSheet.objects.filter(monthly_date__range=[tstart, tend])
            .filter(item_name__item_name__contains="未収金")
            .order_by("item_name")
        )
        # 当月の未収金合計
        total_mishuu_bs = 0
        for d in qs_mishuu_bs:
            total_mishuu_bs += d.amounts

        # 前月の期間を計算。
        lastyear, lastmonth = get_lastmonth(year, month)
        last_tstart, last_tend = select_period(lastyear, lastmonth)
        # 貸借対照表上の前月の未収金
        last_mishuu_bs = (
            BalanceSheet.objects.filter(monthly_date__range=[last_tstart, last_tend])
            .filter(item_name__item_name__contains="未収金")
            .order_by("item_name")
        )
        # 貸借対照表上の前月の未収金合計
        total_last_mishuu = 0
        for d in last_mishuu_bs:
            total_last_mishuu += d.amounts

        # 2024年4月度の処理。Kurasel監査の開始月（2024年4月）前月の未収金は規定値とする。
        if year == settings.START_KURASEL["year"] and month == settings.START_KURASEL["month"]:
            total_last_mishuu = settings.MISHUU_KANRI + settings.MISHUU_SHUUZEN + settings.MISHUU_PARKING

        # 前月の通帳データから前受金を計算する。
        pb_last_maeuke = Transaction.get_maeuke(last_tstart, last_tend)

        # 2024年4月度の処理。Kurasel監査の開始月（2024年4月）前月の前受金は規定値とする。
        if year == settings.START_KURASEL["year"] and month == settings.START_KURASEL["month"]:
            pb_last_maeuke = settings.MAEUKE_INITIAL

        # # 使用する前受金
        # total, maeuke_dict, total_comment = ClaimData.get_maeuke(year, month)

        # 月次収入データ
        context["mr_list"] = qs_mr
        # 入出金明細データ
        context["pb_list"] = qs_pb
        # ネッティング額（相殺処理額）
        context["netting_total"] = netting_total
        # 貸借対照表上の未収金リストと未収金額
        context["mishuu_bs"] = qs_mishuu_bs
        context["total_mishuu_bs"] = total_mishuu_bs
        # 貸借対照表上の前月未収金額
        context["last_mishuu_bs"] = last_mishuu_bs
        context["total_last_mishuu"] = total_last_mishuu
        # 通帳（入出金明細データ）上の前月前受金
        context["pb_last_maeuke"] = pb_last_maeuke
        # # 使用する前受金
        # context["qs_last_maeuke"] = qs_last_maeuke
        # 使用する前受金の合計
        context["total_last_maeuke"] = -total_last_maeuke
        context["total_comment"] = total_comment
        # 月次収入データの合計
        context["total_mr"] = total_mr
        # 入出金明細データの合計（前受金は月次報告で処理のため合計には加えない）
        context["total_pb"] = total_pb + netting_total
        context["total_diff"] = context["total_pb"] - (total_mr - total_last_maeuke + total_last_mishuu)
        context["form"] = form
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["year"] = year
        context["month"] = month

        return context
