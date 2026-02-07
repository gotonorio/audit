import logging

from billing.models import Billing
from control.models import FiscalLock

from .common_service import clean_kurasel_text, parse_records_by_lines

logger = logging.getLogger(__name__)


def execute_billing_import(user, form_data):
    """
    請求合計金額内訳データの取り込みメインロジック
    """
    year = form_data["year"]
    month = form_data["month"]
    mode = form_data["mode"]

    # 決算完了のチェック
    is_frozen = FiscalLock.is_period_frozen(int(year), int(month))
    if is_frozen:
        return (False, {}, [f"{year}年{month}月は既に締められているためデータ読み込みはできません。"])

    # 1. テキスト解析 (2行で1レコード: 項目名、金額)
    lines = clean_kurasel_text(form_data["note"])
    data_list = parse_records_by_lines(lines, 2)
    logger.debug(f"Parsed data_list: {data_list}")

    if not data_list:
        return False, {}, ["取り込むデータが見つかりません。2行1組の形式か確認してください。"]

    # 2. 合計計算
    try:
        total = sum(int(d[1]) for d in data_list)  # data[1]が金額
    except (ValueError, IndexError):
        return False, {}, ["金額部分に数値以外のデータが含まれています。コピー範囲を確認してください。"]

    result_context = {
        "year": year,
        "month": month,
        "mode": mode,
        "data_list": data_list,
        "total": total,
        "author": user.pk,
    }

    if "確認" in mode:
        return True, result_context, []

    # 3. 登録処理
    rtn, error_list = Billing.billing_from_kurasel(result_context)

    if rtn > 0:
        return True, result_context, []
    else:
        return False, result_context, [f"保存失敗: {e}" for e in error_list]
