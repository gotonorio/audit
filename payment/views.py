import datetime
import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic

from kurasel_translator.my_lib.append_list import select_period
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
        local_now = localtime(timezone.now())
        year = self.request.GET.get("year", local_now.year)
        month = self.request.GET.get("month", local_now.month)
        day = self.request.GET.get("day", "00")
        # querysetの作成。
        if day == "00" and month == "0":
            tstart, tend = select_period(year, month)
            qs = Payment.objects.select_related("himoku").filter(payment_date__range=[tstart, tend])
        elif month == "0":
            tstart, tend = select_period(year, month)
            qs = (
                Payment.objects.select_related("himoku")
                .filter(payment_date__range=[tstart, tend])
                .filter(payment_date__day=day)
            )
        elif day == "00":
            tstart, tend = select_period(year, month)
            qs = Payment.objects.select_related("himoku").filter(payment_date__range=[tstart, tend])
        else:
            date_str = str(year) + str(month) + day
            payment_day = datetime.datetime.strptime(date_str, "%Y%m%d")
            qs = Payment.objects.all().select_related("himoku").filter(payment_date=payment_day)
        qs = qs.order_by("payment_date", "himoku__code")
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
            }
        )
        context["approval_list"] = qs
        context["form"] = form
        context["total"] = total
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
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
    success_url = reverse_lazy("payment:payment_list")

    # def form_valid(self, form):
    #     # commitを停止する。
    #     # self.object = form.save(commit=False)
    #     # authorをセット。
    #     # self.object.authorizer = self.request.user
    #     # 入力した日時をセット。
    #     # self.object.approval_date = timezone.now()
    #     # データを保存。
    #     self.object.save()
    #     # messages.success(self.request, "保存しました。")
    #     return super().form_valid(form)


class DeletePaymentView(PermissionRequiredMixin, generic.DeleteView):
    """支払データの削除処理"""

    model = Payment
    template_name = "payment/delete_confirm.html"
    success_url = reverse_lazy("payment:payment_list")
    permission_required = "record.add_transaction"


class PaymentMethodCreateView(PermissionRequiredMixin, generic.CreateView):
    """支払い方法の作成処理"""

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
