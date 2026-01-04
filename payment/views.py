import datetime
import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from passbook.services import select_period

from payment.forms import (
    ApprovalPaymentCreateForm,
    ApprovalPaymentListForm,
    PaymentMethodCreateForm,
)
from payment.models import Payment, PaymentMethod

logger = logging.getLogger(__name__)


class PaymentListView(PermissionRequiredMixin, generic.TemplateView):
    """年月別の承認済み支払いの表示"""

    model = Payment
    template_name = "payment/approval_payment_list.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # GETパラメータ(self.request.GET)
        # .get() で None が返ることを利用して 'or' で繋ぐ
        now = localtime(timezone.now())
        year = self.request.GET.get("year") or now.year
        month = self.request.GET.get("month") or now.month
        day = self.request.GET.get("day") or "0"
        list_order = self.request.GET.get("list_order") or "0"

        year = int(year)
        month = int(month)
        day = int(day)
        list_order = int(list_order)

        # querysetの作成。
        tstart, tend = select_period(year, month)
        if day == 0:
            qs = Payment.objects.select_related("himoku").filter(payment_date__range=[tstart, tend])
        elif month == 0:
            qs = (
                Payment.objects.select_related("himoku")
                .filter(payment_date__range=[tstart, tend])
                .filter(payment_date__day=day)
            )
        else:
            payment_day = datetime.datetime(year, month, day)
            qs = Payment.objects.all().select_related("himoku").filter(payment_date=payment_day)
        # 表示順序
        if list_order == 0:
            qs = qs.order_by("payment_date", "himoku__code")
        else:
            qs = qs.order_by("himoku__code", "payment_date")
        # 支払い金額の合計
        total = 0
        for data in qs:
            total += data.payment
        # forms.pyのKeikakuListFormに初期値を設定する
        form = ApprovalPaymentListForm(
            initial={
                "year": year,
                "month": month,
                "day": day,
                "list_order": list_order,
            }
        )
        context["approval_list"] = qs
        context["form"] = form
        context["total"] = total
        context["year"] = year
        context["month"] = month
        return context


class UpdatePaymentView(PermissionRequiredMixin, generic.UpdateView):
    """支払い承認データ（作成はKuraselからの取り込みなので、修正処理だけが必要）"""

    model = Payment
    form_class = ApprovalPaymentCreateForm
    template_name = "payment/update_form.html"
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True

    # 保存が成功した場合に遷移するurl
    def get_success_url(self):
        qs = Payment.objects.filter(pk=self.object.pk).values("payment_date")
        year = qs[0]["payment_date"].year
        month = qs[0]["payment_date"].month
        return reverse_lazy(
            "payment:payment_list",
            kwargs={"year": year, "month": month},
        )


class PaymentMethodCreateView(PermissionRequiredMixin, generic.CreateView):
    """支払い方法の作成処理
    支払い方法の一覧表示も同じ画面で行う。
    """

    model = PaymentMethod
    form_class = PaymentMethodCreateForm
    template_name = "payment/payment_method_form.html"
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("payment:create_paymentmethod")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = PaymentMethod.objects.all()
        return context


class PaymentMethodUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """支払い方法データの UpdateView"""

    model = PaymentMethod
    form_class = PaymentMethodCreateForm
    template_name = "payment/payment_method_form.html"
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("payment:create_paymentmethod")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = PaymentMethod.objects.all()
        return context
