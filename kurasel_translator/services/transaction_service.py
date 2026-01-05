import datetime
import logging
import unicodedata

from django.conf import settings
from django.utils.http import urlencode
from payment.models import PaymentMethod
from record.models import Himoku, Transaction, TransferRequester

from .common_service import clean_amount_str, clean_kurasel_text

logger = logging.getLogger(__name__)

# --- 共通ユーティリティ ---


# def clean_kurasel_text(note_text):
#     """空行を除去し、各行をストリップしたリストを返す（共通）"""
#     return [line.strip() for line in note_text.splitlines() if line.strip()]


# def clean_amount_str(value):
#     """金額文字列から不要な文字を削除する（共通）"""
#     return value.replace("¥", "").replace("（円）", "").replace(",", "").strip()


# --- 入出金明細固有ロジック ---


def parse_transaction_text(msg_list):
    """
    入出金テキストを解析してレコードごとのリストに分割する
    """
    line_list = []
    for item in msg_list:
        if item == "ホーム":  # 全体コピーの誤混入チェック
            return None
        line_list.append(clean_amount_str(item))

    # 「入金」「出金」を区切り文字としてレコードを分割
    pos_list = [i for i, v in enumerate(line_list) if v in ["入金", "出金"]]

    record_list = []
    end = None
    for start in pos_list[::-1]:  # 後ろからスライスして分割
        record_list.append(line_list[start:end])
        end = start
    return record_list


def normalize_transaction_records(data_list, year):
    """
    日付の変換とUnicode正規化を行う
    """
    rtn_list = []
    for item in data_list:
        # 日付: "01/04" -> datetime.date(2026, 1, 4)
        m, d = item[1].split("/")
        item[1] = datetime.date(year, int(m), int(d))

        # 摘要・依頼人名の正規化 (NFKC)
        # item[4]: 摘要, item[5]: 依頼人名 (存在しない場合は補完)
        if len(item) > 5:
            item[4] = unicodedata.normalize("NFKC", item[4])
            item[5] = unicodedata.normalize("NFKC", item[5])
        else:
            # 依頼人名がない場合は空文字を入れつつ摘要を正規化
            memo = unicodedata.normalize("NFKC", item[4])
            item.append(memo)  # item[5] に正規化した摘要
            item[4] = ""  # item[4] は空

        rtn_list.append(item)
    return rtn_list


def execute_transaction_import(user, form_data):
    """
    入出金取り込みのメイン実行関数
    """
    year = form_data["year"]
    note = form_data["note"]
    mode = form_data["mode"]

    # 1. テキスト解析
    msg_list = clean_kurasel_text(note)
    if not msg_list or msg_list[0] not in ["出金", "入金"]:
        return False, {}, ["データ形式が正しくありません。データ範囲のみをコピーしてください。"]

    raw_records = parse_transaction_text(msg_list)
    if raw_records is None:
        return False, {}, ["「ホーム」等の不要な文字が含まれています。"]

    # 2. データ正規化
    data_list = normalize_transaction_records(raw_records, year)

    # 3. 必要なマスタデータの取得 (Viewから分離)
    default_himoku = Himoku.get_default_himoku()
    if not default_himoku:
        return False, {}, ["デフォルトの費目が設定されていません。"]

    banking_fee_himoku = (
        Himoku.objects.filter(himoku_name="銀行手数料")
        .exclude(accounting_class__accounting_name=settings.COMMUNITY_ACCOUNTING)
        .first()
    )

    context_result = {
        "year": year,
        "mode": mode,
        "data_list": data_list,
        "author": user.pk,
    }

    if "確認" in mode:
        return True, context_result, []

    # 4. 登録処理
    payment_method_list = PaymentMethod.get_paymentmethod_obj()
    requester_list = TransferRequester.get_requester_obj()

    # Modelメソッドの呼び出し
    rtn_month, error_list = Transaction.dwd_from_kurasel(
        context_result,
        payment_method_list,
        requester_list,
        default_himoku,
        banking_fee_himoku,
    )

    if rtn_month > 0:
        return True, {"month": rtn_month, **context_result}, []
    else:
        return False, context_result, [f"失敗: {e}" for e in error_list]
