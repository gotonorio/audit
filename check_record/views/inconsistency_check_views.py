from common.mixins import PeriodParamMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView
from passbook.forms import YearMonthForm

from check_record.services.services import get_expense_inconsistency_summary


class IncosistencyCheckView(PermissionRequiredMixin, PeriodParamMixin, TemplateView):
    """月次支出報告と通帳支払いデータの「不整合チェック
    - PeriodParamMixinを継承してget_year_month_params()を呼び出す。
    """

    template_name = "check_record/expense_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month = self.get_year_month_params()

        # Service層からクリーンなデータを取得
        summary = get_expense_inconsistency_summary(year, month)

        context.update(
            {
                "year": summary["year"],
                "month": summary["month"],
                "yyyymm": f"{summary['year']}年{summary['month']}月",
                "mr_list": summary["mr_list"],
                "total_mr": summary["total_mr"],
                "pb_list": summary["pb_list"],
                "total_pb": summary["total_pb"],
                "form": YearMonthForm(initial={"year": summary["year"], "month": summary["month"]}),
            }
        )
        return context
