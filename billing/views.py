from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.generic import TemplateView
from passbook.forms import YearMonthForm
from passbook.utils import select_period

from .models import Billing


class BillingListView(PermissionRequiredMixin, TemplateView):
    """請求合計金額内訳リスト"""

    template_name = "billing/billing_list.html"
    permission_required = ("record.view_transaction",)
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # GETパラメータ(self.request.GET)
        now = localtime(timezone.now())
        year = self.request.GET.get("year") or now.year
        month = self.request.GET.get("month") or now.month
        year = int(year)
        month = int(month)

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
