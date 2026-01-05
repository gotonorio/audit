import logging

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.timezone import localtime
from django.views.generic.edit import FormView
from kurasel_translator.forms import BalanceSheetTranslateForm
from kurasel_translator.services.balans_sheet_service import execute_bs_import

logger = logging.getLogger(__name__)


class BalanceSheetTransformView(PermissionRequiredMixin, FormView):
    """貸借対照表データの取り込み
    - 年月を指定して取り込む。
    - 取り込みはService層で実施する。
    """

    template_name = "kurasel_translator/bs_translate_form.html"
    form_class = BalanceSheetTranslateForm
    permission_required = "record.add_transaction"

    def get_initial(self):
        """FormViewで、GETパラメータから初期値を設定する"""
        now = localtime(timezone.now())
        return {
            "year": self.request.GET.get("year", now.year),
            "month": self.request.GET.get("month", now.month),
        }

    def form_valid(self, form):
        # Serviceの実行
        success, result_ctx, errors = execute_bs_import(self.request.user, form.cleaned_data)
        context = self.get_context_data(form=form, **result_ctx)

        if not success:
            for msg in errors:
                messages.error(self.request, msg)
            return self.render_to_response(context)

        if "確認" in result_ctx["mode"]:
            # 会計区分の警告などはService側で判定済みだが、必要に応じてここで追加メッセージも可能
            return self.render_to_response(context)

        # 登録成功時
        messages.success(
            self.request,
            f"{result_ctx['year']}年{result_ctx['month']}月度の「{result_ctx['accounting_class']}」貸借対照表を取り込みました。",
        )

        # GETパラメータを付与してリダイレクト
        params = urlencode(
            {
                "year": result_ctx["year"],
                "month": result_ctx["month"],
                "accounting_class": result_ctx["accounting_class"].pk,
            }
        )
        return redirect(f"{reverse('kurasel_translator:create_bs')}?{params}")
