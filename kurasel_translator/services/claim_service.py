import logging

from record.models import ClaimData

from .common_service import clean_kurasel_text

logger = logging.getLogger(__name__)


def parse_claim_text(msg_list, rows_per_record=4):
    """
    テキストリストを4行ごとのレコードに分割し、
    「¥」「部屋番号」などの不要な文字列をクリーンアップする
    """
    record_list = []
    current_record = []

    for line in msg_list:
        # クレンジング処理
        clean_line = (
            line.replace("¥", "").replace(",", "").replace("部屋番号", "").replace("号室", "").strip()
        )
        current_record.append(clean_line)

        # 指定行数（4行）に達したらレコードとして追加
        if len(current_record) == rows_per_record:
            record_list.append(current_record)
            current_record = []

    return record_list


def execute_claim_import(user, form_data):
    """
    請求データ取り込みのメイン実行関数
    Returns: (success_bool, result_context, error_messages)
    """
    year = form_data["year"]
    month = form_data["month"]
    claim_type = form_data["claim_type"]
    mode = form_data["mode"]

    # 1. テキストをリスト化
    lines = clean_kurasel_text(form_data["note"])
    if not lines:
        return False, {}, ["取り込むデータが入力されていません。"]

    # 2. 4行1レコードの構造に変換
    data_list = parse_claim_text(lines, rows_per_record=4)

    # 3. 金額のバリデーションと合計計算
    total = 0
    try:
        for data in data_list:
            # data[3] が請求金額であることを期待
            total += int(data[3])
    except (ValueError, IndexError):
        return False, {}, ["コピー範囲が間違っているか、金額部分に数字以外が含まれています。"]

    result_context = {
        "year": year,
        "month": month,
        "claim_type": claim_type,
        "mode": mode,
        "data_list": data_list,
        "total": total,
        "author": user.pk,
    }

    if "確認" in mode:
        return True, result_context, []

    # 4. 登録処理の実行
    success, error_list = ClaimData.claim_from_kurasel(result_context)
    if success:
        return True, result_context, []
    else:
        errors = [f"取り込み失敗: {e}" for e in error_list]
        return False, result_context, errors
