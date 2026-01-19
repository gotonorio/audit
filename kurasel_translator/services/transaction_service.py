import datetime
import logging
import unicodedata

from django.conf import settings
from django.contrib.auth import get_user_model
from payment.models import PaymentMethod
from record.models import Account, Himoku, Transaction, TransferRequester

from .common_service import clean_amount_str, clean_kurasel_text

logger = logging.getLogger(__name__)

user = get_user_model()

# --- 入出金明細固有ロジック ---


def parse_transaction_text(msg_list):
    """入出金テキストを解析してレコードごとのリストに分割する"""

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

    # 4. 登録処理
    payment_method_list = PaymentMethod.get_paymentmethod_obj()
    # 請求者リスト
    requester_list = TransferRequester.get_requester_obj()

    # 確認モードの場合
    if "確認" in mode:
        return True, context_result, []

    # 登録モード
    rtn_month, error_list = import_transaction_service(
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


def import_transaction_service(data, paymentmethod_list, requester_list, default_himoku, banking_fee_himoku):
    """外部データから取引明細を取り込むメインのサービス関数
    - 戻り値：取り込んだ「月」(int型)。エラーの場合は0を返す。
    - 種類、日付、金額、振り込み依頼人でget_or_createする。
    - 口座は管理会計に決め打ち(id=3)。
    - 費目はdefaultの費目オブジェクト。
    - 勘定科目・費目は手入力となる。
    """
    data_list = data.get("data_list", [])
    if not data_list:
        return 0, []

    # 記録者の取得（エラーハンドリング含む）
    try:
        author_obj = user.objects.get(id=data["author"])
    except user.DoesNotExist:
        logger.error(f"User ID {data['author']} not found.")
        return 0, ["システムエラー: 記録者が見つかりません"]

    error_list = []
    # 最初のデータの月をデフォルトの戻り値にする
    target_month = data_list[0][1].month

    # 処理の高速化と安全性のために一括して口座を取得
    target_account = Account.objects.first()

    for item in data_list:
        # itemの中身を名前付きで定義（可読性向上）
        # [0:種別, 1:日付, 2:金額, 3:残高, 4:振込依頼人, 5:摘要]
        kind, date, amount, balance, requester_name, description = item

        # 1. 費目の特定
        is_income = kind == "入金"
        if is_income:
            himoku_obj = default_himoku
        else:
            himoku_obj = _resolve_expense_himoku(
                requester_name,
                description,
                requester_list,
                paymentmethod_list,
                default_himoku,
                banking_fee_himoku,
            )

        # 2. 保存処理（1件ごとのエラーハンドリング）
        try:
            # get_or_createは副作用があるため慎重に
            _, created = Transaction.objects.get_or_create(
                transaction_date=date,
                amount=amount,
                requesters_name=requester_name,
                defaults={
                    "account": target_account,
                    "is_income": is_income,
                    "himoku": himoku_obj,
                    "balance": balance,
                    "description": description,
                    "author": author_obj,
                },
            )
        except Exception as e:
            logger.error(f"Transaction save error: {e}, Data: {requester_name}")
            error_list.append(requester_name)
            target_month = 0

    return target_month, error_list


def _resolve_expense_himoku(
    name, desc, requester_list, paymentmethod_list, default_himoku, banking_fee_himoku
):
    """
    出金時の費目を優先順位に従って判定する内部関数
    """
    # 優先順位1: 振込依頼人名での完全一致
    for r in requester_list:
        if name == r.requester:
            return r.himoku

    # 優先順位2: 支払い方法（摘要欄）での一致
    for p in paymentmethod_list:
        if desc == p.account_description:
            return p.himoku_name

    logger.debug(desc)
    # 優先順位3: 特定のキーワード（手数料系）
    keywords = ["トリアツカイリヨウ", "フリコミテスウリヨウ"]
    if any(word in desc for word in keywords):
        return banking_fee_himoku

    # どれにも当てはまらない場合はデフォルト
    return default_himoku
