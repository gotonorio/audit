import logging

from django.conf import settings
from passbook.utils import select_period
from record.models import AccountingClass

from monthly_report.models import ReportTransaction

from .base import MonthlyReportBaseView

logger = logging.getLogger(__name__)


class MonthlyReportIncomeListView(MonthlyReportBaseView):
    template_name = "monthly_report/monthly_report_income.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month, ac_class = self.get_year_month_ac(kwargs)

        tstart, tend = select_period(year, month)

        ac_obj = AccountingClass.get_accountingclass_obj(AccountingClass.get_class_name("町内"))

        is_chonaikai = ac_obj.pk == int(ac_class)
        qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "income", is_chonaikai)

        context["transaction_list"] = qs.order_by(
            "himoku__accounting_class",
            "calc_flg",
            "transaction_date",
        )
        context["total_withdrawals"] = ReportTransaction.total_calc_flg(qs)
        context["yyyymm"] = f"第{year - settings.FIRST_PERIOD_YEAR}期{month}月"

        return self.base_context(context, year, month, ac_class)
