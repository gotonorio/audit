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

        # update後にget_success_url()で遷移する場合、kwargsにデータが渡される。typeはint)
        year = self.kwargs.get("year")
        month = self.kwargs.get("month")

        if year is None or month is None:
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)

        # year = str(year)
        # month = str(month)

        # if kwargs:
        #     # update後にget_success_url()で遷移する場合、kwargsにデータが渡される。typeはint)
        #     year = str(self.kwargs.get("year"))
        #     month = str(self.kwargs.get("month"))
        # else:
        #     year = self.request.GET.get("year", localtime(timezone.now()).year)
        #     month = self.request.GET.get("month", localtime(timezone.now()).month)

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
