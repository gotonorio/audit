import logging

from common.mixins import PeriodParamMixin
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import urlencode
from django.views import generic
from passbook.forms import MonthYearSelectionForm
from payment.forms import (
    ApprovalPaymentCreateForm,
    ApprovalPaymentListForm,
    PaymentMethodCreateForm,
)
from payment.models import Payment, PaymentMethod
from payment.services.service import get_payment_summary

logger = logging.getLogger(__name__)


class PaymentAdminBase:
    """支払い管理の共通設定"""

    permission_required = "record.add_transaction"
    raise_exception = True
    success_url = reverse_lazy("payment:create_paymentmethod")


class PaymentListView(PermissionRequiredMixin, PeriodParamMixin, generic.TemplateView):
    """年月別の承認済み支払いの表示
    - PeriodParamMixinを継承してget_year_month_params()を呼び出す。
    """

    template_name = "payment/approval_payment_list.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # common/mixins
        year, month = self.get_year_month_params()
        day = int(self.request.GET.get("day") or 0)
        list_order = int(self.request.GET.get("list_order") or 0)

        # Serviceからデータを取得
        qs, total = get_payment_summary(year, month, day, list_order)

        context.update(
            {
                "approval_list": qs,
                "total": total,
                "year": year,
                "month": month,
                "form": ApprovalPaymentListForm(
                    initial={
                        "year": year,
                        "month": month,
                        "day": day,
                        "list_order": list_order,
                    }
                ),
                # "form": ApprovalPaymentListForm(initial=p),
            }
        )
        return context


class PaymentUpdateView(PaymentAdminBase, PermissionRequiredMixin, generic.UpdateView):
    """支払い承認データの修正"""

    model = Payment
    form_class = ApprovalPaymentCreateForm
    template_name = "payment/update_form.html"

    def get_success_url(self):
        # 保存後、元の年月のリスト画面に戻す
        base_url = reverse("payment:payment_list")
        params = urlencode(
            {
                "year": self.object.payment_date.year,
                "month": self.object.payment_date.month,
            }
        )
        return f"{base_url}?{params}"


class PaymentDeleteByYearMonthView(PaymentAdminBase, PermissionRequiredMixin, generic.FormView):
    """指定された年月の支払いデータを一括削除するFormView"""

    template_name = "payment/payment_delete_by_yearmonth.html"
    form_class = MonthYearSelectionForm
    success_url = reverse_lazy("payment:payment_list")  # 削除後にリダイレクトする先

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            year = form.cleaned_data["year"]
            month = form.cleaned_data["month"]

            # 「実行ボタン」が押された場合のみ削除
            if "execute_delete" in request.POST:
                count = Payment.delete_by_yearmonth(year, month)
                messages.success(request, f"{year}年{month}月のデータを {count} 件削除しました。")
                return redirect(self.get_success_url())

            # 「確認ボタン」が押された場合は、データを抽出して同じページを表示
            target_data = Payment.objects.filter(payment_date__year=year, payment_date__month=month)
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    target_data=target_data,
                    confirm_mode=True,  # 確認モードフラグ
                    year=year,
                    month=month,
                )
            )
        return self.form_invalid(form)


class PaymentMethodBase(PaymentAdminBase):
    """支払い方法設定画面の共通ロジック（一覧表示を同梱）"""

    model = PaymentMethod
    form_class = PaymentMethodCreateForm
    template_name = "payment/payment_method_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = PaymentMethod.objects.all()
        return context


class PaymentMethodCreateView(PaymentMethodBase, PermissionRequiredMixin, generic.CreateView):
    """支払い方法の作成"""

    pass


class PaymentMethodUpdateView(PaymentMethodBase, PermissionRequiredMixin, generic.UpdateView):
    """支払い方法の更新"""

    pass
