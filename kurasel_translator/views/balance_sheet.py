import logging

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.generic.edit import FormView
from kurasel_translator.forms import BalanceSheetTranslateForm
from monthly_report.models import BalanceSheet
from passbook.utils import redirect_with_param
from record.models import AccountingClass

logger = logging.getLogger(__name__)


def list_to_dict(data_list):
    """ListからDictを作成する
    - [key1, value1, key2, value2,....]のリストから、
    - {'key1':'value1', 'key2':'value2',..... }の辞書を作成して返す。
    """
    bs_dict = {}
    for i in range(0, len(data_list), 2):
        key = data_list[i]
        value = data_list[i + 1]
        bs_dict[key] = value
    return bs_dict


class BalanceSheetTranslateView(PermissionRequiredMixin, FormView):
    """貸借対照表データの取り込み
    - 年月を指定して取り込む。
    - 取り込みはget_or_create()を使う。
    """

    # テンプレート名の設定
    template_name = "kurasel_translator/bs_translate_form.html"
    # フォームの設定（月次収支データ用のFormを利用する）
    form_class = BalanceSheetTranslateForm
    permission_required = "record.add_transaction"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 年月既定値
        form = BalanceSheetTranslateForm(
            initial={
                "year": localtime(timezone.now()).year,
                "month": localtime(timezone.now()).month,
            }
        )
        context["form"] = form
        return context

    def form_valid(self, form):
        year = form.cleaned_data["year"]
        month = form.cleaned_data["month"]
        accounting_class = form.cleaned_data["accounting_class"]
        mode = form.cleaned_data["mode"]
        note = form.cleaned_data["note"]
        # msgを’\r\n'で区切ってリストを作成する。
        tmp_list = note.splitlines()
        # tmp_listから空の要素を削除する。
        msg_list = [a for a in tmp_list if a != ""]

        # コピーした貸借対照表データのチェック。
        error_msg = self.check_bs_data(msg_list, form)
        if error_msg:
            # エラーがあった場合、messageを作成してデータを破棄する。
            messages.add_message(self.request, messages.ERROR, error_msg)
            msg_list = []
            context = {
                "form": form,
            }
            return render(self.request, self.template_name, context)
        else:
            # 先頭行（会計区分名）を読み込んで、先頭行を削除。
            ac_class = msg_list.pop(0)

        # データ行の正規化
        asset_list, debt_list = self.bs_translate(msg_list)
        # Dictに変換
        asset_dict = list_to_dict(asset_list)
        debt_dict = list_to_dict(debt_list)
        bs_dict = dict(asset_dict, **debt_dict)

        context = {
            "form": form,
            "bs_dict": bs_dict,
            "year": year,
            "month": month,
            "accounting_class": accounting_class,
            "author": self.request.user.pk,
        }
        if "確認" in mode:
            # 確認モードの場合、会計区分のチェックをして表示のみを行う。（accounting_classのtypeに注意）
            if str(accounting_class) != ac_class:
                msg = f"{ac_class} != {accounting_class} 会計区分を見直してください"
                messages.add_message(self.request, messages.ERROR, msg)
            return render(self.request, self.template_name, context)
        else:
            # 登録モードの場合、ReportTransactionモデルクラス関数でデータ保存する
            rtn, error_list = BalanceSheet.bs_from_kurasel(accounting_class, context)
            if rtn:
                msg = f"{year}年{month}月度の貸借対照表の取り込みが完了しました。"
                messages.add_message(self.request, messages.ERROR, msg)
                # 取り込みに成功したら、一覧表表示する。
                ac_pk = AccountingClass.objects.get(accounting_name=accounting_class).pk
                url = redirect_with_param(
                    "monthly_report:bs_table",
                    dict(year=year, month=str(month).zfill(2), ac_class=ac_pk),
                )
                return redirect(url)
            else:
                # msg = f'月次収支データの取り込みに失敗しました。費目名 ＝ {error_list[0]}'
                for i in error_list:
                    msg = f"月次収支データの取り込みに失敗しました。{i}"
                    messages.add_message(self.request, messages.ERROR, msg)
                # 取り込みに失敗したら、取り込み画面に戻る。
                return render(self.request, self.template_name, context)

    def bs_translate(self, msg_list):
        """Kuraselの表示をコピペで取り込む
        - "¥"マーク、"（円）"、","の3つを削除。
        - strip()は最後に行う。
        """
        assetflg = True
        asset_list = []
        debt_list = []
        for line in msg_list:
            line = line.replace("¥", "").replace("（円）", "").replace(",", "").strip()
            if line in ["資産の部"]:
                continue
            if line in ["負債・剰余金の部", "負債の部"]:
                assetflg = False
                continue
            # if line == '剰余金の部':
            if line == "負債の部合計":
                # 取り込み処理を終了する。
                break
            if assetflg:
                asset_list.append(line)
            else:
                debt_list.append(line)
        return asset_list, debt_list

    def check_bs_data(self, msg_list, form):
        """コピーした貸借対照表データのチェック
        - 1行目は会計区分「管理費会計」「修繕積立金会計」「駐車場会計」「町内会費会計」となる。
        """
        # 取り込んだデータの1行目が「資産の部」であることを確認する。
        if msg_list[0] in ("管理費会計", "修繕積立金会計", "駐車場会計", "町内会費会計"):
            return False
        else:
            msg = "タイトルの「会計区分名」から「剰余の部合計」までをコピーしてください"
            return msg
