import logging

from common.services import select_period
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic

from monthly_report.forms import MonthlyReportViewForm
from monthly_report.services import monthly_report_services
from monthly_report.services.monthly_report_services import get_monthly_report_queryset

logger = logging.getLogger(__name__)


class YearIncomeExpenseListView(PermissionRequiredMixin, generic.TemplateView):
    """収支リスト 年間表示"""

    template_name = "monthly_report/year_income_expenselist.html"
    permission_required = ("budget.view_expensebudget",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # formで戻った場合、requestからデータを取り出す。
        year = self.request.GET.get("year", localtime(timezone.now()).year)
        ac_class = self.request.GET.get("ac_class") or 0
        year = int(year)
        ac_class = int(ac_class)

        # 抽出期間（monthが"all"なら1年分）
        tstart, tend = select_period(year, 0)

        # 収入
        qs_income = get_monthly_report_queryset(tstart, tend, ac_class, "income", False)
        # 月次報告収入の月別合計を計算。
        mr_income_total = monthly_report_services.monthly_total(qs_income, int(year), "amount")
        # 年間合計を計算してmr_income_totalに追加する。
        mr_income_total["income_year_total"] = sum(mr_income_total.values())
        context["mr_income_total"] = mr_income_total

        # 支出
        qs_expense = get_monthly_report_queryset(tstart, tend, ac_class, "expense", False)
        # 月次報告支出の月別合計を計算。 aggregateは辞書を返す。
        mr_expense_total = monthly_report_services.monthly_total(qs_expense, int(year), "amount")
        # 年間合計を計算してmr_totalに追加する。
        mr_expense_total["expense_year_total"] = sum(mr_expense_total.values())
        context["mr_expense_total"] = mr_expense_total

        # form 初期値を設定
        form = MonthlyReportViewForm(
            initial={
                "year": year,
                "ac_class": ac_class,
            }
        )
        context["form"] = form
        context["year"] = year
        # 会計区分が''だった場合の処理
        if ac_class == "":
            ac_class = "0"
        context["ac"] = ac_class
        return context
