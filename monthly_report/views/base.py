from control.models import ControlRecord
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic

from monthly_report.forms import MonthlyReportViewForm


class MonthlyReportBaseView(PermissionRequiredMixin, generic.TemplateView):
    permission_required = ("budget.view_expensebudget",)

    def get_year_month_ac(self, kwargs):
        # update後にget_success_url()で遷移する場合、kwargsにデータが渡される。typeはint)
        # URL引数(self.kwargs) or 2. GETパラメータ(self.request.GET) or 3. デフォルト
        # .get() で None が返ることを利用して 'or' で繋ぐ
        now = localtime(timezone.now())
        year = self.kwargs.get("year") or self.request.GET.get("year") or now.year
        month = self.kwargs.get("month") or self.request.GET.get("month") or now.month
        ac_class = self.kwargs.get("ac_class") or self.request.GET.get("accounting_class") or "0"

        year = int(year)
        month = int(month)
        ac_class = int(ac_class)

        return year, month, ac_class

    def base_context(self, context, year, month, ac_class):
        context["form"] = MonthlyReportViewForm(
            initial={
                "year": year,
                "month": month if month else None,
                "accounting_class": ac_class,
            }
        )
        context["year"] = year
        context["month"] = month
        context["ac"] = ac_class
        context["delete_flg"] = ControlRecord.get_delete_flg()
        return context
