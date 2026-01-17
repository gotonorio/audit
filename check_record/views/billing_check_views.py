import logging

from common.mixins import PeriodParamMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView
from passbook.forms import YearMonthForm

from check_record.services.services import get_billing_check_service

logger = logging.getLogger(__name__)


class BillingAmountCheckView(PermissionRequiredMixin, PeriodParamMixin, TemplateView):
    """請求金額内訳データと月次報告比較リスト
    - PeriodParamMixinを継承してget_year_month_params()を呼び出す。
    """

    template_name = "check_record/billing_income_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month = self.get_year_month_params()

        # Service層からクリーンなデータを取得
        summary = get_billing_check_service(year, month)

        # 請求金額内訳データ
        context.update(
            {
                "billing_list": summary["billing_list"],
                "billing_total": summary["billing_total"],
                "check_mismatch": summary["check_mismatch"],
                "mr_list": summary["mr_list"],
                "total_mr": summary["total_mr"],
                "total_mishuu_claim": summary["total_mishuu_claim"],
                "form": YearMonthForm(initial={"year": summary["year"], "month": summary["month"]}),
                "yyyymm": str(year) + "年" + str(month) + "月",
                "year": year,
                "month": month,
            }
        )
        return context
