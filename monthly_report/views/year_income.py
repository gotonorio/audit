import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from monthly_report.forms import MonthlyReportViewForm
from monthly_report.services import monthly_report_services
from passbook.utils import select_period

logger = logging.getLogger(__name__)


class YearIncomeListView(PermissionRequiredMixin, generic.TemplateView):
    """月次報告収入リスト 年間表示"""

    template_name = "monthly_report/year_incomelist.html"
    permission_required = ("budget.view_expensebudget",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            # 年間収入画面から遷移した場合、kwargsにデータが渡される。(typeはint)
            year = str(self.kwargs.get("year"))
            ac_class = str(self.kwargs.get("ac_class"))
        else:
            # formで戻った場合、requestからデータを取り出す。（typeはstr、ALLは""となる）
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            ac_class = self.request.GET.get("accounting_class", "0")
            # ac_classが「空」の場合の処理
            if ac_class == "":
                ac_class = "0"

        # 抽出期間（monthが"all"なら1年分）
        tstart, tend = select_period(year, 0)
        qs, mr_total = monthly_report_services.qs_year_income(tstart, tend, ac_class, False)
        context["mr_total"] = mr_total

        # form 初期値を設定
        form = MonthlyReportViewForm(
            initial={
                "year": year,
                "accounting_class": ac_class,
            }
        )
        context["transaction_list"] = qs
        context["form"] = form
        context["yyyymm"] = str(year) + "年"
        context["year"] = year
        # 会計区分が''だった場合の処理
        if ac_class == "":
            ac_class = "0"
        context["ac"] = ac_class
        return context
