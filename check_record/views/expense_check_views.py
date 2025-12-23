import logging

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from monthly_report.models import BalanceSheet, ReportTransaction
from passbook.forms import YearMonthForm
from passbook.utils import check_period, get_lastmonth, select_period
from record.models import Transaction

logger = logging.getLogger(__name__)


class MonthlyReportExpenseCheckView(PermissionRequiredMixin, generic.TemplateView):
    """月次収支の支出データと口座支出データの月別比較リスト"""

    template_name = "check_record/kurasel_mr_expense_check.html"
    permission_required = ("record.view_transaction",)

    # templateファイルの切り替え
    def get_template_names(self):
        """templateファイルを切り替える"""
        if self.request.user_agent_flag == "mobile":
            template_name = "check_record/mobile/mobile_mr_expense_check.html"
        else:
            template_name = "check_record/kurasel_mr_expense_check.html"
        return [template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            year = self.kwargs.get("year")
            month = self.kwargs.get("month")
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
        # 入出金明細データとの比較のため町内会会計を含める（2025-08-01）
        # ---------------------------------------------------------------------
        qs_mr = ReportTransaction.get_qs_mr(tstart, tend, "0", "expense", True)
        # 月次収支報告の支出リスト（相殺項目を除外する）
        qs_mr = qs_mr.exclude(is_netting=True)
        # 月次収支報告の支出合計（集計フラグがFalseの費目を除外する）
        total_mr = ReportTransaction.total_calc_flg(qs_mr.exclude(himoku__aggregate_flag=False))

        # ---------------------------------------------------------------------
        # 入出金明細の支出データ
        # ---------------------------------------------------------------------
        qs_pb = Transaction.get_qs_pb(tstart, tend, "0", "0", "expense", True, False)
        qs_pb = qs_pb.order_by("transaction_date", "himoku__code", "description")
        # 通帳データの合計（集計フラグがTrueの費目合計）
        total_pb = 0
        for d in qs_pb:
            # 費目名が「不明」、「町内会」の場合も考慮する
            if d.himoku and d.himoku.aggregate_flag and not d.himoku.is_community:
                total_pb += d.amount

        # ---------------------------------------------------------------------
        # 当月の未払い
        # ---------------------------------------------------------------------
        qs_this_miharai, total_this_miharai = BalanceSheet.get_miharai_bs(tstart, tend)

        # ---------------------------------------------------------------------
        # 前月の未払金
        # ---------------------------------------------------------------------
        _, total_last_miharai = BalanceSheet.get_miharai_bs(last_tstart, last_tend)

        # 2023年4月（Kurasel監査の開始月）前月の未払金
        if int(year) == settings.START_KURASEL["year"] and int(month) == settings.START_KURASEL["month"]:
            total_last_miharai = settings.MIHARAI_INITIAL

        context["mr_list"] = qs_mr
        context["pb_list"] = qs_pb
        context["total_mr"] = total_mr
        context["total_pb"] = total_pb
        context["total_diff"] = total_pb - total_mr - total_last_miharai
        context["this_miharai"] = qs_this_miharai
        context["total_this_miharai"] = total_this_miharai
        context["total_last_miharai"] = total_last_miharai
        context["form"] = form
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["year"] = year
        context["month"] = month

        return context


class YearReportExpenseCheckView(PermissionRequiredMixin, generic.TemplateView):
    """月次報告の年間支出データと口座支出データの比較リスト"""

    template_name = "check_record/year_expense_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            year = self.kwargs.get("year")
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)

        # formの初期値を設定する。
        form = YearMonthForm(
            initial={
                "year": year,
            }
        )
        # 当月の抽出期間
        tstart, tend = select_period(year, 0)

        # ---------------------------------------------------------------------
        # (1) 月次報告の支出リスト
        # ---------------------------------------------------------------------
        mr_year_expense = ReportTransaction.get_year_expense(tstart, tend)
        # 支出のない費目は除く
        mr_year_expense = mr_year_expense.exclude(amount=0)
        # 年間支出の合計
        # 「費目の集計フラグ」「レコードの集計フラグ」のどちらかが「False」の場合は合計に含める。
        total_mr_expense = 0
        for i in mr_year_expense:
            if i["himoku__aggregate_flag"] and i["calc_flg"]:
                total_mr_expense += i["price"]

        # ---------------------------------------------------------------------
        # (2) 入出金明細（通帳データ）の支出リスト
        # ---------------------------------------------------------------------
        pb_year_expense = Transaction.get_year_expense(tstart, tend)
        pb_year_expense = pb_year_expense.order_by("himoku")

        # ---------------------------------------------------------------------
        # (3) 当年12月の貸借対照表による未払い
        # ---------------------------------------------------------------------
        tstart_12 = timezone.datetime(int(year), 12, 1, 0, 0, 0)
        tend_12 = timezone.datetime(int(year), 12, 31, 0, 0, 0)
        qs_this_miharai, total_this_miharai = BalanceSheet.get_miharai_bs(tstart_12, tend_12)

        # 支出合計金額
        total_pb_expense = 0
        for i in pb_year_expense:
            total_pb_expense += i["price"]

        # 月次収入データ
        context["year_list"] = mr_year_expense
        # 月次収入データの合計
        context["total_mr"] = total_mr_expense
        # 通帳支出データ
        context["pb_list"] = pb_year_expense
        # 通帳支出データの合計
        context["total_pb"] = total_pb_expense
        # 合計の差額（未払金）
        context["miharai"] = total_mr_expense - total_pb_expense
        # form
        context["form"] = form
        # 当年の貸借対照表（未払金）
        context["this_miharai"] = qs_this_miharai
        context["total_this_miharai"] = total_this_miharai
        context["year"] = year

        # # 前年12月の未払金
        # context["total_last_miharai"] = total_last_miharai
        # # 当年12月の未払金
        # context["total_this_miharai"] = total_this_miharai

        return context
