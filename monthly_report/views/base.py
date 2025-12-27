from control.models import ControlRecord
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from monthly_report.forms import MonthlyReportViewForm


class MonthlyReportBaseView(PermissionRequiredMixin, generic.TemplateView):
    permission_required = ("budget.view_expensebudget",)

    def get_year_month_ac(self, kwargs):
        if kwargs:
            year = int(self.kwargs.get("year"))
            month = int(self.kwargs.get("month", 0))
            ac_class = self.kwargs.get("ac_class", "0")
        else:
            now = localtime(timezone.now())
            year = int(self.request.GET.get("year", now.year))
            month = int(self.request.GET.get("month", now.month))
            ac_class = self.request.GET.get("accounting_class", "0")

        if ac_class == "":
            ac_class = "0"

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
