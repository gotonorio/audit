import logging

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.generic.edit import FormView
from kurasel_translator.forms import ClaimTranslateForm
from record.models import ClaimData

logger = logging.getLogger(__name__)


class ClaimTransformView(PermissionRequiredMixin, FormView):
    """請求時初期データ（未収金、前受金、振替不備）の読み込み"""

    # テンプレート名の設定
    template_name = "kurasel_translator/claim_translate_form.html"
    # フォームの設定
    form_class = ClaimTranslateForm
    permission_required = "record.add_transaction"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = localtime(timezone.now())
        year = self.request.GET.get("year") or now.year
        month = self.request.GET.get("month") or now.month
        year = int(year)
        month = int(month)

        # 年月既定値
        form = ClaimTranslateForm(
            initial={
                "year": year,
                "month": month,
            }
        )
        context["form"] = form
        return context

    def form_valid(self, form):
        year = form.cleaned_data["year"]
        month = form.cleaned_data["month"]
        claim_type = form.cleaned_data["claim_type"]
        mode = form.cleaned_data["mode"]
        note = form.cleaned_data["note"]
        # msgを’\r\n'で区切ってリストを作成する。
        tmp_list = note.splitlines()
        # tmp_listから空の要素を削除する。
        msg_list = [a for a in tmp_list if a != ""]
        # 支払管理の場合、4行で1レコード。(区分所有者、部屋番号、氏名、請求金額)
        data_list = self.normalize_claim(msg_list, 4)
        context = {
            "form": form,
            "data_list": data_list,
            "year": year,
            "month": month,
            "claim_type": claim_type,
            "mode": mode,
            "author": self.request.user.pk,
        }
        if data_list is None:
            return render(self.request, self.template_name, context)
        # # ここで取り込んだKuraselのデータの1行目の3列目が数字かどうかで、ヘッダーかどうかチェックする。
        # if data_list[0][3].isdigit() is False:
        #     msg = "ヘッダーが含まれています。ヘッダーを除いてコピーしてください"
        #     messages.add_message(self.request, messages.ERROR, msg)
        if "確認" in mode:
            # 合計を計算
            try:
                total = 0
                for data in data_list:
                    total += int(data[3])
            except ValueError:
                err_msg = "コピー範囲が間違っているようです。データ本体だけをコピーしてください。"
                messages.add_message(self.request, messages.ERROR, err_msg)
            context["total"] = total
            # 確認モードの場合、表示のみを行う。
            return render(self.request, self.template_name, context)
        else:
            # 登録モードの場合、ClaimDataモデルクラス関数でデータ保存する
            rtn, error_list = ClaimData.claim_from_kurasel(context)
            if rtn:
                msg = f"{year}-{month}-{claim_type}の承認済み支払いデータの取り込みが完了しました。"
                messages.add_message(self.request, messages.ERROR, msg)
                # # 保存成功後に遷移する場合のパラメータ
                # param = dict(year=year, month=str(month).zfill(2))
                # # 取り込みに成功したら、一覧表表示する。
                # url = redirect_with_param("payment:payment_list", param)
                # return redirect(url)
                return redirect("register:master_page")
            else:
                for i in error_list:
                    msg = f"データの取り込みに失敗しました。{i}"
                    messages.add_message(self.request, messages.ERROR, msg)
                # 取り込みに失敗したら、取り込み画面に戻る。
                return render(self.request, self.template_name, context)

    def normalize_claim(self, msg_list, row):
        """Kuraselの表示をコピペで取り込んだデータの正規化を行う。
        - "¥"マーク、","の2つを削除。
        - 余計な文字を削除。
        - strip()は最後に行う。
        """
        cnt = 0
        record_list = []
        line_list = []
        for line in msg_list:
            line_list.append(
                line.replace("¥", "")
                .replace(",", "")
                .replace("部屋番号", "")
                .replace("号室", "")
                # .replace("（区分所有者）", "")
                .strip()
            )
            cnt += 1
            if cnt == row:
                record_list.append(line_list)
                cnt = 0
                line_list = []
        return record_list
