import datetime
import logging
import unicodedata

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, render
from django.views.generic.edit import FormView

from kurasel_translator.forms import (
    BalanceSheetTranslateForm,
    DepositWithdrawalForm,
    MonthlyBalanceForm,
    PaymentAuditForm,
)
from kurasel_translator.my_lib import append_list
from monthly_report.models import BalanceSheet, ReportTransaction
from payment.models import Payment, PaymentMethod
from record.models import AccountingClass, Himoku, Transaction, TransferRequester

logger = logging.getLogger(__name__)


def check_accountingtype(data, ac, kind):
    """取り込んだ月次収支データのチェック
    - d[0] : 費目名
    - ac   : 会計区分
    - kind : 収入 or 支出
    """
    for d in data:
        if (
            d[0] in settings.KANRI_INCOME
            and kind in settings.KANRI_INCOME
            and ac in settings.KANRI_INCOME
        ):
            return True
        elif (
            d[0] in settings.KANRI_PAYMENT
            and kind in settings.KANRI_PAYMENT
            and ac in settings.KANRI_PAYMENT
        ):
            return True
        elif (
            d[0] in settings.SHUUZEN_INCOME
            and kind in settings.SHUUZEN_INCOME
            and ac in settings.SHUUZEN_INCOME
        ):
            return True
        elif (
            d[0] in settings.SHUUZEN_PAYMENT
            and kind in settings.SHUUZEN_PAYMENT
            and ac in settings.SHUUZEN_PAYMENT
        ):
            return True
        elif (
            d[0] in settings.PARKING_INCOME
            and kind in settings.PARKING_INCOME
            and ac in settings.PARKING_INCOME
        ):
            return True
        elif (
            d[0] in settings.PARKING_PAYMENT
            and kind in settings.PARKING_PAYMENT
            and ac in settings.PARKING_PAYMENT
        ):
            return True
    return False


class MonthlyBalanceView(PermissionRequiredMixin, FormView):
    """月次収支データの取り込み
    - 年月を指定して取り込む。
    - 取り込みはget_or_create()を使う。
    """

    # テンプレート名の設定
    template_name = "kurasel_translator/monthlybalance_form.html"
    # フォームの設定
    form_class = MonthlyBalanceForm
    permission_required = "record.add_transaction"

    def form_valid(self, form):
        year = form.cleaned_data["year"]
        month = form.cleaned_data["month"]
        accounting_class = form.cleaned_data["accounting_class"]
        kind = form.cleaned_data["kind"]
        mode = form.cleaned_data["mode"]
        msg = form.cleaned_data["note"]
        # msgを’\r\n'で区切ってリストを作成する。
        tmp_list = msg.splitlines()
        # tmp_listから空の要素を削除する。
        msg_list = [a for a in tmp_list if a != ""]
        # 月次収支の場合、5行で1レコード。
        data_list = self.translate(msg_list, 5)
        # ここで取り込んだKuraselのデータの1行目の3列目が数字かどうかで、ヘッダーかどうかチェックする。
        if data_list[0][2].isdigit() is False:
            msg = "ヘッダーが含まれています。ヘッダーを除いてコピーしてください"
            messages.add_message(self.request, messages.ERROR, msg)
        # 最下行の合計行が含まれているかチェックする。
        if "合計" in data_list[-1][0]:
            msg = "最下行の合計が選択されているようです。最下行を除いてコピーしてください"
            messages.add_message(self.request, messages.ERROR, msg)

        # 会計区分をチェックする。（accounting_classのtypeに注意）
        chk = check_accountingtype(data_list, str(accounting_class), kind)
        if chk is False:
            msg = "「会計区分」または「収入・支出区分」を確認してください。"
            messages.add_message(self.request, messages.ERROR, msg)

        context = {
            "form": form,
            "data_list": data_list,
            "year": year,
            "month": month,
            "kind": kind,
            "mode": mode,
            "author": self.request.user.id,
        }
        if "確認" in mode:
            # 合計を計算
            total = 0
            for data in data_list:
                total += int(data[2])
            context["total"] = total
            # 確認モードの場合、表示のみを行う。
            return render(self.request, self.template_name, context)
        else:
            # 登録モードの場合、ReportTransactionモデルクラス関数でデータ保存する
            rtn, error_list = ReportTransaction.monthly_from_kurasel(accounting_class, context)
            if rtn:
                msg = "月次収支データの取り込みが完了しました。"
                messages.add_message(self.request, messages.ERROR, msg)
                ac_id = AccountingClass.objects.get(accounting_name=accounting_class).id
                # 保存成功後に遷移する場合のパラメータ。受け取りはkwargs.get["year"]とする。
                param = dict(
                    year=year, month=str(month).zfill(2), ac_class=ac_id
                )
                # 取り込みに成功したら、一覧表表示する。
                if kind == "収入":
                    # 収入データの取り込みに成功したら、一覧表表示する。
                    url = append_list.redirect_with_param(
                        "monthly_report:incomelist", param
                    )
                    return redirect(url)
                else:
                    # 支出データの取り込みに成功したら、一覧表表示する。
                    url = append_list.redirect_with_param(
                        "monthly_report:expenselist", param
                    )
                    return redirect(url)
            else:
                # msg = f'月次収支データの取り込みに失敗しました。費目名 ＝ {error_list[0]}'
                for i in error_list:
                    msg = f"月次収支データの取り込みに失敗しました。{i}"
                    messages.add_message(self.request, messages.ERROR, msg)
                # 取り込みに失敗したら、取り込み画面に戻る。
                return render(self.request, self.template_name, context)

    def translate(self, msg_list, row):
        """Kuraselの表示をコピペで取り込む
        - "¥"マーク、"（円）"、","の3つを削除。
        - strip()は最後に行う。
        """
        cnt = 0
        record_list = []
        line_list = []
        for line in msg_list:
            line_list.append(
                line.replace("¥", "").replace("（円）", "").replace(",", "").strip()
            )
            cnt += 1
            if cnt == row:
                record_list.append(line_list)
                cnt = 0
                line_list = []
        return record_list


class DepositWithdrawalView(MonthlyBalanceView):
    """入出金明細データの取込み
    - 取り込みはget_or_create()を使う。
    - 摘要欄等に加筆した場合、重複読み込みされるのでデータチェックは必要。
    """

    template_name = "kurasel_translator/depositwithdrawal_form.html"
    form_class = DepositWithdrawalForm

    def form_valid(self, form):
        mode = form.cleaned_data["mode"]
        year = form.cleaned_data["year"]
        msg = form.cleaned_data["note"]
        # msgを行末コードで区切ってリストを作成する。
        tmp_list = msg.splitlines()
        # tmp_listから空の要素を削除する。
        msg_list = [a for a in tmp_list if a != ""]

        # 入出金明細では、最初の要素は「出金」「入金」となるはず。
        if not msg_list[0] in ["出金", "入金"]:
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
            "author": self.request.user.id,
        }
        if "確認" in mode:
            return render(self.request, self.template_name, context)
        else:
            """登録モードの場合、ReportTransactionモデルクラス関数でデータ保存する"""
            # 費目推定のためPaymentMethodのオブジェクトを作成。
            payment_method_list = PaymentMethod.get_paymentmethod_obj()
            # 費目名推定のためrequesterのオブジェクトを作成。
            requester_list = TransferRequester.get_requester_obj()
            # 入出金入出金明細データの取り込み。
            rtn, error_list = Transaction.dwd_from_kurasel(
                context, payment_method_list, requester_list
            )
            if rtn:
                msg = "データの取り込みが完了しました。"
                messages.add_message(self.request, messages.ERROR, msg)
                # 取り込みに成功したら、一覧表表示する。
                return redirect("record:transaction_list")
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


class PaymentAuditView(PermissionRequiredMixin, FormView):
    """支払承認済みデータの読み込み"""

    # テンプレート名の設定
    template_name = "kurasel_translator/payment_audit_form.html"
    # フォームの設定
    form_class = PaymentAuditForm
    permission_required = "record.add_transaction"

    def form_valid(self, form):
        year = form.cleaned_data["year"]
        month = form.cleaned_data["month"]
        day = form.cleaned_data["day"]
        mode = form.cleaned_data["mode"]
        msg = form.cleaned_data["note"]
        # msgを’\r\n'で区切ってリストを作成する。
        tmp_list = msg.splitlines()
        # tmp_listから空の要素を削除する。
        msg_list = [a for a in tmp_list if a != ""]
        # 支払管理の場合、4行で1レコード。(状況、摘要、支払先、支払い金額)
        data_list = self.translate_payment(msg_list, 4)
        # Himokuマスターから費目名のListを作成
        himoku_list = list(Himoku.get_himoku_list())
        # 取り込んだデータに費目名を追加
        data_list = self.set_himoku(data_list, himoku_list)
        # ここで取り込んだKuraselのデータの1行目の3列目が数字かどうかで、ヘッダーかどうかチェックする。
        if data_list[0][3].isdigit() is False:
            msg = "ヘッダーが含まれています。ヘッダーを除いてコピーしてください"
            messages.add_message(self.request, messages.ERROR, msg)
        context = {
            "form": form,
            "data_list": data_list,
            "year": year,
            "month": month,
            "day": day,
            "mode": mode,
            "author": self.request.user.id,
        }
        if "確認" in mode:
            # 合計を計算
            total = 0
            for data in data_list:
                total += int(data[3])
            context["total"] = total
            # 確認モードの場合、表示のみを行う。
            return render(self.request, self.template_name, context)
        else:
            # 登録モードの場合、ReportTransactionモデルクラス関数でデータ保存する
            rtn, error_list = Payment.payment_from_kurasel(context)
            if rtn:
                msg = f"{year}-{month}-{day}の承認済み支払いデータの取り込みが完了しました。"
                messages.add_message(self.request, messages.ERROR, msg)
                # 保存成功後に遷移する場合のパラメータ
                param = dict(year=year, month=str(month).zfill(2))
                # 取り込みに成功したら、一覧表表示する。
                url = append_list.redirect_with_param("payment:payment_list", param)
                return redirect(url)
                # return redirect('payment:payment_list')
            else:
                for i in error_list:
                    msg = f"データの取り込みに失敗しました。{i}"
                    messages.add_message(self.request, messages.ERROR, msg)
                # 取り込みに失敗したら、取り込み画面に戻る。
                return render(self.request, self.template_name, context)

    def translate_payment(self, msg_list, row):
        """Kuraselの表示をコピペで取り込む
        - "¥"マーク、","の2つを削除。
        - strip()は最後に行う。
        """
        cnt = 0
        record_list = []
        line_list = []
        for line in msg_list:
            line_list.append(line.replace("¥", "").replace(",", "").strip())
            cnt += 1
            if cnt == row:
                record_list.append(line_list)
                cnt = 0
                line_list = []
        return record_list

    def set_himoku(self, data_list, himoku_list):
        """取り込んだ支払データで摘要欄に費目名が含まれていたら、費目名を追加する"""
        new_data_list = []
        for data in data_list:
            chk = True
            for himoku in himoku_list:
                if himoku in data[1]:
                    data.append(himoku)
                    chk = False
                    break
            if chk:
                data.append("不明")
            new_data_list.append(data)
        return new_data_list


class BalanceSheetTranslateView(FormView):
    """貸借対照表データの取り込み
    - 年月を指定して取り込む。
    - 取り込みはget_or_create()を使う。
    """

    # テンプレート名の設定
    template_name = "kurasel_translator/bs_translate_form.html"
    # フォームの設定（月次収支データ用のFormを利用する）
    form_class = BalanceSheetTranslateForm

    def form_valid(self, form):
        year = form.cleaned_data["year"]
        month = form.cleaned_data["month"]
        accounting_class = form.cleaned_data["accounting_class"]
        mode = form.cleaned_data["mode"]
        msg = form.cleaned_data["note"]
        # msgを’\r\n'で区切ってリストを作成する。
        tmp_list = msg.splitlines()
        # tmp_listから空の要素を削除する。
        msg_list = [a for a in tmp_list if a != ""]

        # コピーした貸借対照表データのチェック。
        error_msg = self.check_bs_data(msg_list, form)
        if error_msg:
            # エラーがあった場合
            messages.add_message(self.request, messages.ERROR, error_msg)
            msg_list = []

        # データ行の正規化
        asset_list, debt_list = self.bs_translate(msg_list)
        # Dictに変換
        asset_dict = append_list.list_to_dict(asset_list)
        debt_dict = append_list.list_to_dict(debt_list)
        bs_dict = dict(asset_dict, **debt_dict)

        context = {
            "form": form,
            "bs_dict": bs_dict,
            "year": year,
            "month": month,
            "mode": mode,
            "author": self.request.user.id,
        }
        if "確認" in mode:
            # 確認モードの場合、表示のみを行う。
            return render(self.request, self.template_name, context)
        else:
            # 登録モードの場合、ReportTransactionモデルクラス関数でデータ保存する
            rtn, error_list = BalanceSheet.bs_from_kurasel(accounting_class, context)
            if rtn:
                msg = f"{year}年{month}月度の貸借対照表の取り込みが完了しました。"
                messages.add_message(self.request, messages.ERROR, msg)
                # 取り込みに成功したら、一覧表表示する。
                ac_id = AccountingClass.objects.get(accounting_name=accounting_class).id
                url = append_list.redirect_with_param(
                    "monthly_report:bs_table",
                    dict(year=year, month=str(month).zfill(2), accounting_class=ac_id),
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
        """コピーした貸借対照表データのチェック"""
        # 取り込んだデータの1行目が「資産の部」であることを確認する。
        if msg_list[0] in ("資産の部",):
            return False
        else:
            msg = "データコピーの範囲が間違っています。「資産の部」から「剰余の部」までをコピーしてください"
            return msg
