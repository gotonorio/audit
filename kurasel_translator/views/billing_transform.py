import logging

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.timezone import localtime
from django.views.generic.edit import FormView
from kurasel_translator.services.billing_service import execute_billing_import
from passbook.forms import KuraselTranslatorForm

logger = logging.getLogger(__name__)


class BillingTransformView(PermissionRequiredMixin, FormView):
    template_name = "kurasel_translator/billing_form.html"
    form_class = KuraselTranslatorForm
    permission_required = "record.add_transaction"

    def get_initial(self):
        now = localtime(timezone.now())
        return {
            "year": self.request.GET.get("year", now.year),
            "month": self.request.GET.get("month", now.month),
        }

    def form_valid(self, form):
        # Serviceの実行
        success, result_ctx, errors = execute_billing_import(self.request.user, form.cleaned_data)

        if not success:
            for msg in errors:
                messages.error(self.request, msg)
            # 失敗時は入力画面に戻す
            return self.render_to_response(self.get_context_data(form=form, **result_ctx))

        if "確認" in result_ctx["mode"]:
            return self.render_to_response(self.get_context_data(form=form, **result_ctx))

        # 登録成功時
        messages.success(
            self.request,
            f"{result_ctx['year']}年{result_ctx['month']}月度の, 請求合計金額内訳データの取り込みが完了しました。",
        )
        # GETパラメータを付与してリダイレクト
        params = urlencode(
            {
                "year": result_ctx["year"],
                "month": result_ctx["month"],
            }
        )
        return redirect(f"{reverse('billing:billing_list')}?{params}")
