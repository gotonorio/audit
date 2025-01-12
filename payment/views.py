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
        if kwargs:
            # 遷移で表示された時。（kwargsにデータが渡される）
            year = str(kwargs.get("year"))
            month = str(kwargs.get("month"))
            day = self.request.GET.get("day", "00")
            # 表示順は入力されないので、日付順をデフォルトとして設定する。
            list_order = "0"
        else:
            # 画面が表示された時、年月を指定して表示した時。
            local_now = localtime(timezone.now())
            year = self.request.GET.get("year", str(local_now.year))
            month = self.request.GET.get("month", str(local_now.month))
            day = self.request.GET.get("day", "00")
            list_order = self.request.GET.get("list_order", "0")
        # querysetの作成。
        tstart, tend = select_period(year, month)
        if day == "00":
            qs = Payment.objects.select_related("himoku").filter(payment_date__range=[tstart, tend])
        elif month == "0":
            qs = (
                Payment.objects.select_related("himoku")
                .filter(payment_date__range=[tstart, tend])
                .filter(payment_date__day=day)
            )
        else:
            date_str = str(year) + str(month) + day
            payment_day = datetime.datetime.strptime(date_str, "%Y%m%d")
            qs = Payment.objects.all().select_related("himoku").filter(payment_date=payment_day)
        # 表示順序
        if list_order == "0":
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
