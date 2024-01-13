import datetime
import logging

import jpholiday
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic

from check_record.forms import KuraselCheckForm
from kurasel_translator.my_lib.append_list import select_period

# from check_record.views.views import get_lastmonth
from monthly_report.models import BalanceSheet, ReportTransaction
from payment.models import Payment
from record.models import Transaction

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
            # update後にget_success_url()で遷移する場合、kwargsにデータが渡される)
            year = kwargs.get("year")
            month = kwargs.get("month")
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)

        # Kuraselによる会計処理は2023年4月以降。それ以前は表示しない。
        if int(year) < settings.START_KURASEL["year"] or (
            int(year) <= settings.START_KURASEL["year"] and int(month) < settings.START_KURASEL["month"]
        ):
            year = settings.START_KURASEL["year"]
            month = settings.START_KURASEL["month"]
            context["warning_kurasel"] = "Kuraselでの会計処理は2023年4月以降です。"

        # formの初期値を設定する。
        form = KuraselCheckForm(
            initial={
                "year": year,
                "month": int(month),
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
        qs_pb = Transaction.get_qs_pb(tstart, tend, "", "", "expense", False)
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
        context["year"] = int(year)
        context["month"] = str(month)

        return context


class MonthlyReportExpenseCheckView(PermissionRequiredMixin, generic.TemplateView):
    """月次収支の支出データと口座支出データの月別比較リスト"""

    template_name = "check_record/kurasel_mr_expense_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            # update後にget_success_url()で遷移する場合、kwargsにデータが渡される)
            year = kwargs.get("year")
            month = kwargs.get("month")
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)

        # Kuraselによる会計処理は2023年4月以降。それ以前は表示しない。
        if int(year) < settings.START_KURASEL["year"] or (
            int(year) <= settings.START_KURASEL["year"] and int(month) < settings.START_KURASEL["month"]
        ):
            year = settings.START_KURASEL["year"]
            month = settings.START_KURASEL["month"]
            context["warning_kurasel"] = "Kuraselでの会計処理は2023年4月以降です。"

        # formの初期値を設定する。
        form = KuraselCheckForm(
            initial={
                "year": year,
                "month": int(month),
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
        qs_mr, _ = ReportTransaction.get_monthly_report_expense(tstart, tend)
        # 支出のない費目は除く
        qs_mr = qs_mr.filter(ammount__gt=0)
        # 月次収支の支出合計（ネッティング処理の費目を控除する）
        qs_mr_without_netting = qs_mr.exclude(is_netting=True)
        total_mr = ReportTransaction.calc_total_withflg(qs_mr_without_netting, True)
        # 入出金明細の支出データ
        qs_pb = Transaction.get_qs_pb(tstart, tend, "", "", "expense", True)
        qs_pb = qs_pb.order_by("transaction_date", "himoku__code")
        # 通帳データの合計（集計フラグがTrueの費目合計）
        total_pb = 0
        for d in qs_pb:
            if d.himoku.aggregate_flag:
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

        # Kurasel監査の開始月前月の未払金
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
        context["year"] = int(year)
        context["month"] = str(month)

        return context


class MonthlyReportIncomeCheckView(PermissionRequiredMixin, generic.TemplateView):
    """月次収支の収入データと口座収入データの月別比較リスト"""

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
            # update後にget_success_url()で遷移する場合、kwargsにデータが渡される)
            year = kwargs.get("year")
            month = kwargs.get("month")
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)

        # 追加contextデータの初期化
        context["netting_total"] = 0
        context["last_maeuke"] = 0
        context["total_maeuke"] = 0
        context["total_mishuu"] = 0
        context["total_last_mishuu"] = 0
        context["total_mr"] = 0
        context["total_pb"] = 0

        # Kuraselによる会計処理は2023年4月以降。
        if int(year) < settings.START_KURASEL["year"] or (
            int(year) <= settings.START_KURASEL["year"] and int(month) < settings.START_KURASEL["month"]
        ):
            month = str(settings.START_KURASEL["month"]).zfill(2)
            context["warning_kurasel"] = "Kuraselでの会計処理は2023年4月以降です。"

        # formの初期値を設定する。
        form = KuraselCheckForm(
            initial={
                "year": year,
                "month": int(month),
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
        # 月次収支の収入データを抽出
        #
        qs_mr, _ = ReportTransaction.get_monthly_report_income(tstart, tend)
        # 収入のない費目は除く
        qs_mr = qs_mr.filter(ammount__gt=0)

        # 月次収支の収入合計
        total_mr = ReportTransaction.calc_total_withflg(qs_mr, True)

        #
        # 入出金明細データ（通帳データ）の収入リスト
        # 監査用補正データも含めて抽出する。2023-08-21
        #
        qs_pb = Transaction.get_qs_pb(tstart, tend, "", "", "income", True)
        # 2023年3月以前のデータを除外する。
        start_date = datetime.date(2023, 4, 1)
        qs_pb = qs_pb.filter(transaction_date__gte=start_date)
        # 資金移動は除く
        qs_pb = qs_pb.filter(himoku__aggregate_flag=True).order_by("transaction_date", "himoku")
        # 収入合計金額
        total_pb, _ = Transaction.calc_total(qs_pb)

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
        qs_this_mishuu = (
            BalanceSheet.objects.filter(monthly_date__range=[tstart, tend])
            .filter(item_name__item_name__contains="未収金")
            .order_by("item_name")
        )
        # 当月の未収金合計
        total_mishuu = 0
        for d in qs_this_mishuu:
            total_mishuu += d.amounts

        # 前月の期間を計算。
        lastyear, lastmonth = get_lastmonth(year, month)
        last_tstart, last_tend = select_period(lastyear, lastmonth)
        # 前月の未収金
        last_mishuu = (
            BalanceSheet.objects.filter(monthly_date__range=[last_tstart, last_tend])
            .filter(item_name__item_name__contains="未収金")
            .order_by("item_name")
        )
        # 前月の未収金合計
        total_last_mishuu = 0
        for d in last_mishuu:
            total_last_mishuu += d.amounts

        # Kurasel監査の開始月前月の未収金
        if int(year) == settings.START_KURASEL["year"] and int(month) == settings.START_KURASEL["month"]:
            total_last_mishuu = settings.MISHUU_KANRI + settings.MISHUU_SHUUZEN + settings.MISHUU_PARKING

        # 前月の通帳データから前受金を計算する。
        last_maeuke = Transaction.get_maeuke(last_tstart, last_tend)

        # Kurasel監査の開始月前月の前受金
        if int(year) == settings.START_KURASEL["year"] and int(month) == settings.START_KURASEL["month"]:
            last_maeuke = settings.MAEUKE_INITIAL

        context["mr_list"] = qs_mr
        context["netting_total"] = netting_total
        context["this_mishuu"] = qs_this_mishuu
        context["total_mishuu"] = total_mishuu
        context["last_mishuu"] = last_mishuu
        context["total_last_mishuu"] = total_last_mishuu
        context["last_maeuke"] = last_maeuke
        context["pb_list"] = qs_pb
        context["total_mr"] = total_mr
        context["total_pb"] = total_pb
        context["total_diff"] = total_pb - total_mr
        context["form"] = form
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["year"] = int(year)
        context["month"] = str(month)

        return context
