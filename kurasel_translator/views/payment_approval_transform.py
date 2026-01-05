import logging

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.timezone import localtime
from django.views.generic.edit import FormView
from kurasel_translator.forms import PaymentAuditForm
from kurasel_translator.services.approval_service import execute_payment_approval_import

logger = logging.getLogger(__name__)


class PaymentApprovalTransformView(PermissionRequiredMixin, FormView):
    template_name = "kurasel_translator/payment_audit_form.html"
    form_class = PaymentAuditForm
    permission_required = "record.add_transaction"

    def get_initial(self):
        now = localtime(timezone.now())
        return {
            "year": self.request.GET.get("year", now.year),
            "month": self.request.GET.get("month", now.month),
        }

    def form_valid(self, form):
        # Serviceの呼び出し
        success, result_ctx, errors = execute_payment_approval_import(self.request.user, form.cleaned_data)

        if not success:
            for msg in errors:
                messages.error(self.request, msg)
            return self.render_to_response(self.get_context_data(form=form, **result_ctx))

        if "確認" in result_ctx["mode"]:
            return self.render_to_response(self.get_context_data(form=form, **result_ctx))

        # 登録成功時
        messages.success(
            self.request,
            f"{result_ctx['year']}-{result_ctx['month']}-{result_ctx['day']}の承認済みデータの取り込みが完了しました。",
        )

        # GETパラメータでリダイレクト
        params = urlencode(
            {
                "year": result_ctx["year"],
                "month": result_ctx["month"],
                "day": 10,
                "list_order": 0,
            }
        )
        return redirect(f"{reverse('payment:payment_list')}?{params}")
