import logging

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.generic.edit import FormView
from kurasel_translator.forms import ClaimTranslateForm
from kurasel_translator.services.claim_service import execute_claim_import

logger = logging.getLogger(__name__)


class ClaimTransformView(PermissionRequiredMixin, FormView):
    template_name = "kurasel_translator/claim_translate_form.html"
    form_class = ClaimTranslateForm
    permission_required = "record.add_transaction"

    def get_initial(self):
        now = localtime(timezone.now())
        return {
            "year": self.request.GET.get("year", now.year),
            "month": self.request.GET.get("month", now.month),
        }

    def form_valid(self, form):
        # Serviceの実行
        success, result_ctx, errors = execute_claim_import(self.request.user, form.cleaned_data)

        if not success:
            for msg in errors:
                messages.error(self.request, msg)
            return self.render_to_response(self.get_context_data(form=form, **result_ctx))

        if "確認" in result_ctx["mode"]:
            return self.render_to_response(self.get_context_data(form=form, **result_ctx))

        # 登録成功時
        msg = f"{result_ctx['year']}-{result_ctx['month']}-{result_ctx['claim_type']} のデータ取り込みが完了しました。"
        messages.success(self.request, msg)

        return redirect("register:master_page")
