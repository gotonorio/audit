import logging

from control.models import FiscalLock
from payment.models import Payment
from record.models import Himoku

from .common_service import clean_kurasel_text, parse_records_by_lines

logger = logging.getLogger(__name__)


def guess_himoku_from_summary(data_list):
    """
    摘要欄(data[1])に費目名が含まれているかチェックし、
    一致すればその費目名を、なければデフォルト(不明)を付与する
    """
    himoku_list = list(Himoku.get_himoku_list())
    default_himoku = Himoku.get_default_himoku()

    if not default_himoku:
        raise ValueError("デフォルトの費目名が設定されていません。")

    default_name = default_himoku.himoku_name

    for data in data_list:
        summary = data[1]
        matched_name = next((h for h in himoku_list if h in summary), default_name)
        data.append(matched_name)  # data[4] に費目名を追加

    return data_list


def execute_payment_approval_import(user, form_data):
    """
    支払承認データの取り込みメインロジック
    """
    year = form_data["year"]
    month = form_data["month"]
    day = form_data["day"]
    mode = form_data["mode"]

    # 決算完了のチェック
    is_frozen = FiscalLock.is_period_frozen(int(year), int(month))
    if is_frozen:
        return (False, {}, [f"{year}年{month}月は既に締められているためデータ読み込みはできません。"])

    # 1. 解析と分割 (4行で1レコード)
    lines = clean_kurasel_text(form_data["note"])
    data_list = parse_records_by_lines(lines, 4)

    if not data_list:
        return False, {}, ["取り込むデータがありません。"]

    # 2. ヘッダーチェック (金額列が数字かどうか)
    if not data_list[0][3].isdigit():
        return False, {}, ["ヘッダーが含まれています。データ部分のみコピーしてください。"]

    # 3. 費目推測
    try:
        data_list = guess_himoku_from_summary(data_list)
    except ValueError as e:
        return False, {}, [str(e)]

    # 4. 合計計算
    total = sum(int(d[3]) for d in data_list)

    result_context = {
        "year": year,
        "month": month,
        "day": day,
        "mode": mode,
        "data_list": data_list,
        "total": total,
        "author": user.pk,
    }

    if "確認" in mode:
        return True, result_context, []

    # 5. 登録実行
    success, error_list = Payment.payment_from_kurasel(result_context)
    if success:
        return True, result_context, []
    else:
        return False, result_context, [f"保存失敗: {e}" for e in error_list]
