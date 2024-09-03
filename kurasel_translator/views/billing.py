import logging

from billing.models import Billing
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.generic.edit import FormView
from passbook.forms import KuraselTranslatorForm

logger = logging.getLogger(__name__)


class BillingIntakeView(PermissionRequiredMixin, FormView):
    """請求合計金額内訳データの取込み"""

    template_name = "kurasel_translator/billing_form.html"
    form_class = KuraselTranslatorForm
    permission_required = "record.add_transaction"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 年月既定値
        form = KuraselTranslatorForm(
            initial={
                "year": localtime(timezone.now()).year,
                "month": localtime(timezone.now()).month,
            }
        )
        context["form"] = form
        return context

    def form_valid(self, form):
        mode = form.cleaned_data["mode"]
        year = form.cleaned_data["year"]
        month = form.cleaned_data["month"]
        note = form.cleaned_data["note"]
        # msgを行末コードで区切ってリストを作成する。
        tmp_list = note.splitlines()
        # tmp_listから空の要素を削除する。
        msg_list = [a for a in tmp_list if a != ""]
        # データの正規化を行う。
        data_list = self.translate_billing(msg_list, 2)

        # ここで取り込んだKuraselのデータを処理する
        context = {
            "form": form,
            "data_list": data_list,
            "year": year,
            "month": month,
            "mode": mode,
            "author": self.request.user.pk,
        }

        # 確認・取り込み処理
        if "確認" in mode:
            return render(self.request, self.template_name, context)
        else:
            """登録モードの場合、Billingモデルクラス関数でデータ保存する"""
            # 請求合計金額内訳データの取り込み。
            rtn, error_list = Billing.billing_from_kurasel(context)
            if rtn > 0:
                msg = "データの取り込みが完了しました。"
                messages.add_message(self.request, messages.ERROR, msg)
                # 取り込みに成功したら、一覧表表示する。
                return redirect("billing:billing_list", year=year, month=month)
            else:
                for i in error_list:
                    msg = f"データの取り込みに失敗しています。{i}"
                    messages.add_message(self.request, messages.ERROR, msg)
                # 取り込みに失敗したら、取り込み画面に戻る。
                return render(self.request, self.template_name, context)

    def translate_billing(self, msg_list, row):
        """Kuraselの入出金(deposit and withdrawals)データをコピペで取り込む。
        - "¥"マーク、"（円）"、","の3つを削除。strip()は最後に行う。
        - "入金"、"出金"キーワードで分割する。
        - 振り込み依頼人名と摘要を合わせて摘要とする。
        """
        cnt = 0
        record_list = []
        line_list = []

        for line in msg_list:
            line_list.append(line.replace("¥", "").replace("（円）", "").replace(",", "").strip())
            cnt += 1
            if cnt == row:
                record_list.append(line_list)
                cnt = 0
                line_list = []
        return record_list
