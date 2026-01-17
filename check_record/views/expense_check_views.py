# check_record/views.py

from common.mixins import PeriodParamMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView
from passbook.forms import YearMonthForm

from check_record.services.expense_check_service import (
    get_monthly_expense_check_data,
    get_yearly_expense_check_data,
)


class MonthlyReportExpenseCheckView(PermissionRequiredMixin, PeriodParamMixin, TemplateView):
    """月次収支の支出データと口座支出データの月別比較リスト
    - PeriodParamMixinを継承してget_year_month_params()を呼び出す。
    """

    template_name = "check_record/kurasel_mr_expense_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month = self.get_year_month_params()

        # Service層で集計
        data = get_monthly_expense_check_data(year, month)

        # 差額の計算: (実際の出金) - (報告上の費用) - (前月からの未払解消分)
        total_diff = data["total_pb"] - data["total_mr"] - data["total_last_miharai"]

        context.update(
            {
                "year": data["year"],
                "month": data["month"],
                "yyyymm": f"{data['year']}年{data['month']}月",
                "mr_list": data["qs_mr"],
                "pb_list": data["qs_pb"],
                "total_mr": data["total_mr"],
                "total_pb": data["total_pb"],
                "total_diff": total_diff,
                "this_miharai": data["qs_this_miharai"],
                "total_this_miharai": data["total_this_miharai"],
                "total_last_miharai": data["total_last_miharai"],
                "form": YearMonthForm(initial={"year": data["year"], "month": data["month"]}),
            }
        )
        return context


class YearReportExpenseCheckView(PermissionRequiredMixin, PeriodParamMixin, TemplateView):
    """月次報告の年間支出データと口座支出データの比較リスト
    - PeriodParamMixinを継承してget_year_month_params()を呼び出す。
    """

    template_name = "check_record/year_expense_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, _ = self.get_year_month_params()

        # Service層で集計
        summary = get_yearly_expense_check_data(year)

        context.update(
            {
                "year": year,
                "year_list": summary["year_list"],
                "total_mr": summary["total_mr"],
                "pb_list": summary["pb_list"],
                "total_pb": summary["total_pb"],
                "miharai": summary["total_mr"] - summary["total_pb"],  # 報告書支出と通帳出金の差
                "this_miharai": summary["this_miharai_list"],
                "total_this_miharai": summary["total_this_miharai"],
                "form": YearMonthForm(initial={"year": year}),
            }
        )
        return context
