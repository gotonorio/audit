import datetime
import logging
import unicodedata

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.generic.edit import FormView
from kurasel_translator.forms import (
    DepositWithdrawalForm,
)
from payment.models import PaymentMethod
from record.models import (
    Himoku,
    Transaction,
    TransferRequester,
)

logger = logging.getLogger(__name__)


class DepositWithdrawalTransformView(PermissionRequiredMixin, FormView):
    """入出金明細データの取込み
    - 取り込みはget_or_create()を使う。
    - 摘要欄等に加筆した場合、重複読み込みされるのでデータチェックは必要。
    """

    template_name = "kurasel_translator/depositwithdrawal_form.html"
    form_class = DepositWithdrawalForm
    permission_required = "record.add_transaction"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 年月既定値
        form = DepositWithdrawalForm(
            initial={
                "year": localtime(timezone.now()).year,
            }
        )
        context["form"] = form
        return context

    def form_valid(self, form):
        mode = form.cleaned_data["mode"]
        year = form.cleaned_data["year"]
        note = form.cleaned_data["note"]
        # msgを行末コードで区切ってリストを作成する。
        tmp_list = note.splitlines()
        # tmp_listから空の要素を削除する。
        msg_list = [a for a in tmp_list if a != ""]

        # 入出金明細では、最初の要素は「出金」「入金」となるはず。
        if msg_list[0] not in ["出金", "入金"]:
            msg = f"「{msg_list[0]}」が含まれています。データだけをコピーしてください"
            messages.add_message(self.request, messages.ERROR, msg)
            return render(
                self.request,
                self.template_name,
                {"form": form, "year": year, "mode": mode},
            )

        data_list = self.translate_dwd(msg_list)
        if data_list is False:
            msg = "入出金データのみコピーしてください。"
            messages.add_message(self.request, messages.ERROR, msg)
            return render(
                self.request,
                self.template_name,
                {"form": form, "year": year, "mode": mode},
            )
        # 日付のフォーマットを調整する。
        data_list = self.adjust_date(data_list, year)
        # ここで取り込んだKuraselのデータを処理する
        context = {
            "form": form,
            "data_list": data_list,
            "year": year,
            "mode": mode,
            "author": self.request.user.pk,
        }
        # デフォルトの費目オブジェクトを準備する。
        default_himoku = Himoku.get_default_himoku()
        if default_himoku is None:
            messages.info(
                self.request,
                "defaultの費目名が設定されていません。管理者に連絡してください",
            )
            return render(self.request, self.template_name, context)
        # 銀行手数料の費目オブジェクト
        banking_fee_himoku = (
            Himoku.objects.filter(himoku_name="銀行手数料")
            .exclude(accounting_class__accounting_name=settings.COMMUNITY_ACCOUNTING)
            .get()
        )

        # 確認・取り込み処理
        if "確認" in mode:
            return render(self.request, self.template_name, context)
        else:
            """登録モードの場合、ReportTransactionモデルクラス関数でデータ保存する"""
            # (1) 支払い方法から費目推定のためPaymentMethodのオブジェクトを作成。
            payment_method_list = PaymentMethod.get_paymentmethod_obj()
            # (2) 振込依頼人名から費目推定のためrequesterのオブジェクトを作成。
            requester_list = TransferRequester.get_requester_obj()
            # 入出金入出金明細データの取り込み。
            rtn, error_list = Transaction.dwd_from_kurasel(
                context,
                payment_method_list,
                requester_list,
                default_himoku,
                banking_fee_himoku,
            )
            if rtn > 0:
                msg = "データの取り込みが完了しました。"
                messages.add_message(self.request, messages.ERROR, msg)
                # 取り込みに成功したら、一覧表表示する。
                return redirect("record:transaction_list", year=year, month=rtn, list_order=0, himoku_id=0)
            else:
                for i in error_list:
                    msg = f"データの取り込みに失敗しています。{i}"
                    messages.add_message(self.request, messages.ERROR, msg)
                # 取り込みに失敗したら、取り込み画面に戻る。
                return render(self.request, self.template_name, context)

    def adjust_date(self, data_list, year):
        """Kuraselの入出金データを正規化する
        - 文字列 -> datetime.date
        - 半角カナ -> 全角かな
        """
        rtn_list = []
        for item in data_list:
            # 日付を正規化
            md = item[1].split("/")
            item[1] = datetime.date(year, int(md[0]), int(md[1]))
            # 摘要と（存在するならば）振込依頼人名をUnicode正規化する。
            if len(item) > 5:
                # 振込依頼人名が存在する場合Unicode正規化する。
                item[4] = unicodedata.normalize("NFKC", item[4])
                item[5] = unicodedata.normalize("NFKC", item[5])
            else:
                # item[5]とitem[4]の順番に注意。
                item.append("")
                item[5] = unicodedata.normalize("NFKC", item[4])
                item[4] = ""
            rtn_list.append(item)
        return rtn_list

    def translate_dwd(self, msg_list):
        """Kuraselの入出金(deposit and withdrawals)データをコピペで取り込む。
        - "¥"マーク、"（円）"、","の3つを削除。strip()は最後に行う。
        - "入金"、"出金"キーワードで分割する。
        - 振り込み依頼人名と摘要を合わせて摘要とする。
        """
        record_list = []
        line_list = []
        # 正規化した要素のリストを作成する。（半角カナは後で処理する）
        for item in msg_list:
            # 全体コピーで取り込んだ場合、Falseを返して関数を抜ける。
            if item in ["ホーム"]:
                return False
            # 不要な文字を削除。
            line_list.append(item.replace("（円）", "").replace(",", "").strip())
        # 「入金」、「出金」要素の位置を調べる。
        pos_list = []
        for i, value in enumerate(line_list):
            if value in ["入金", "出金"]:
                pos_list.append(i)
        # 入出金レコードのリストを生成する。スライスを使って逆順に取り出す。
        end = None
        for start in pos_list[::-1]:
            tmp_list = line_list[start:end]
            end = start
            record_list.append(tmp_list)

        return record_list
