from control.models import ControlRecord
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic

from monthly_report.forms import MonthlyReportViewForm


class MonthlyReportBaseView(PermissionRequiredMixin, generic.TemplateView):
    permission_required = ("budget.view_expensebudget",)

    def get_year_month_ac(self, kwargs):
        # GETパラメータ(self.request.GET)

        now = localtime(timezone.now())
        year = self.request.GET.get("year") or now.year
        month = self.request.GET.get("month") or now.month
        ac_class = self.request.GET.get("ac_class") or "0"

        year = int(year)
        month = int(month)
        ac_class = int(ac_class)

        return year, month, ac_class

    def base_context(self, context, year, month, ac_class):
        context["form"] = MonthlyReportViewForm(
            initial={
                "year": year,
                "month": month if month else None,
                "ac_class": ac_class,
            }
        )
        context["year"] = year
        context["month"] = month
        context["ac"] = ac_class
        context["delete_flg"] = ControlRecord.get_delete_flg()
        return context
