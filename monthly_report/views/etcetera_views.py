from control.models import ControlRecord
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from passbook.utils import select_period
from record.models import AccountingClass

from monthly_report.forms import MonthlyReportViewForm
from monthly_report.models import ReportTransaction
from monthly_report.services import monthly_report_services


class CalcFlgCheckList(PermissionRequiredMixin, generic.TemplateView):
    """合計計算から除外している項目リスト
    - calc_flg（計算対象フラグ）がFalse
    - 細目レベルでis_aggregareがFalse
    """

    template_name = "monthly_report/calcflg_check_list.html"
    permission_required = "record.add_transaction"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.GET.get("year", localtime(timezone.now()).year)
        # 抽出期間
        tstart, tend = select_period(year, 0)
        # 合計計算除外項目リスト（calc_flg=False, aggregate_flag=False）
        qs = ReportTransaction.get_calcflg_check(tstart, tend)
        # 除外項目の合計
        total = 0
        for i in qs:
            total += i.amount
        # formに初期値を設定する
        form = MonthlyReportViewForm(
            initial={
                "year": year,
            }
        )
        context["calcflg_off_list"] = qs
        context["total"] = total
        context["form"] = form
        context["year"] = year
        return context


class CheckOffset(PermissionRequiredMixin, generic.TemplateView):
    """「口座振替手数料」の相殺処理のフラグをチェック"""

    template_name = "monthly_report/chk_offset.html"
    permission_required = "record.add_transaction"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.GET.get("year", localtime(timezone.now()).year)
        # 抽出期間
        tstart, tend = select_period(year, 0)
        # 費目名「口座振替手数料」でfilter
        offset_himoku_name = ControlRecord.get_offset_himoku()
        if offset_himoku_name is None:
            messages.info(self.request, "相殺処理する費目が設定されていません。")
        # 期間と相殺処理する費目名でfiler
        qs = (
            ReportTransaction.objects.all()
            .filter(transaction_date__range=[tstart, tend])
            .filter(himoku__himoku_name=offset_himoku_name)
            .order_by("-transaction_date")
        )
        form = MonthlyReportViewForm(
            initial={
                "year": year,
            }
        )
        context["chk_obj"] = qs
        context["form"] = form
        return context


class UnpaidBalanceListView(PermissionRequiredMixin, generic.TemplateView):
    """未払金一覧"""

    template_name = "monthly_report/unpaid_list.html"
    permission_required = "record.add_transaction"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.GET.get("year", localtime(timezone.now()).year)
        # 抽出期間
        tstart, tend = select_period(year, 0)
        # 未払金リスト
        qs = ReportTransaction.get_unpaid_balance(tstart, tend)
        # 未払金の合計
        total = 0
        for i in qs:
            total += i.amount
        # formに初期値を設定する
        form = MonthlyReportViewForm(
            initial={
                "year": year,
            }
        )
        context["unpaid_list"] = qs
        context["total"] = total
        context["form"] = form
        context["year"] = year
        return context


class SimulatonDataListView(PermissionRequiredMixin, generic.TemplateView):
    """長期修繕計画シミュレーション用データリスト
    - 長期修繕計画シミュレーション用データとして、修繕積立金会計と駐車場会計の実績収入リストを表示する。
    """

    template_name = "monthly_report/simulation_data.html"
    permission_required = ("record.add_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.GET.get("year") or localtime(timezone.now()).year

        # 抽出期間（年間）
        tstart, tend = select_period(year, 0)
        # 修繕積立金会計クラスID
        ac_shuuzen = AccountingClass.objects.get(accounting_name="修繕積立金会計")
        ac_parking = AccountingClass.objects.get(accounting_name="駐車場会計")

        # 修繕積立金会計「その他収入」リスト
        qs_others_income, others_income_total = monthly_report_services.qs_year_income(
            tstart, tend, ac_shuuzen.pk, True
        )
        context["others_income_total"] = others_income_total

        # 駐車場会計
        qs_parking, parking_total = monthly_report_services.qs_year_income(tstart, tend, ac_parking.pk, False)
        context["parking_total"] = parking_total

        # form 初期値を設定
        form = MonthlyReportViewForm(
            initial={
                "year": year,
            }
        )
        context["others_income_list"] = qs_others_income
        context["parking_income_list"] = qs_parking
        context["form"] = form
        context["yyyymm"] = str(year) + "年"
        context["year"] = year
        return context
