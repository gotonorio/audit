import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView
from passbook.forms import YearMonthForm

from check_record.mixins import IncomeCheckParamMixin
from check_record.services import get_apploval_check_service

logger = logging.getLogger(__name__)


class ApprovalExpenseCheckView(PermissionRequiredMixin, IncomeCheckParamMixin, TemplateView):
    """支払い承認データと入出金明細データの月別比較リスト
    - 入出金データの合計では、承認不要費目（資金移動、共用部電気料等）を除外する。
    - 未払金（貸借対照表データ）の表示。
    """

    template_name = "check_record/kurasel_ap_expense_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year, month = self.get_params()

        # Service層からクリーンなデータを取得
        summary = get_apploval_check_service(year, month)

        # 支払い承認データをtemplateへ送る
        context.update(
            {
                "mr_list": summary["mr_list"],
                "pb_list": summary["pb_list"],
                "total_mr": summary["total_mr"],
                "total_pb": summary["total_pb"],
                "total_diff": summary["total_pb"] - summary["total_mr"],
                "this_miharai": summary["this_miharai"],
                "this_miharai_total": summary["this_miharai_total"],
                "last_miharai_total": summary["last_miharai_total"],
                "form": YearMonthForm(initial={"year": summary["year"], "month": summary["month"]}),
                "yyyymm": str(year) + "年" + str(month) + "月",
                "year": year,
                "month": month,
            }
        )
        return context
