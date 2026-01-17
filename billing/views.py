from common.mixins import PeriodParamMixin
from common.services import select_period
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView
from passbook.forms import YearMonthForm

from .models import Billing


class BillingListView(PeriodParamMixin, PermissionRequiredMixin, TemplateView):
    """請求合計金額内訳リスト
    - PeriodParamMixinを継承してget_year_month_params()を呼び出す。
    """

    template_name = "billing/billing_list.html"
    permission_required = ("record.view_transaction",)
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # GETパラメータ(self.request.GET)
        year, month = self.get_year_month_params()

        # 抽出期間
        tstart, tend = select_period(year, month)
        # 請求合計金額内訳データの抽出
        qs = Billing.get_billing_list(tstart, tend)
        # 表示順序
        qs = qs.order_by(
            "billing_item__code",
        )
        # 合計金額
        total_billing = Billing.calc_total_billing(qs)
        # forms.pyのKeikakuListFormに初期値を設定する
        form = YearMonthForm(
            initial={
                "year": year,
                "month": month,
            }
        )
        context["billing_list"] = qs
        context["form"] = form
        context["total_billing"] = total_billing
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["year"] = year
        context["month"] = month

        return context
