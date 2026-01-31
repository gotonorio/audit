import logging

from common.services import select_period
from control.models import ControlRecord
from django.conf import settings
from monthly_report.models import ReportTransaction
from record.models import Himoku

logger = logging.getLogger(__name__)


def translate_kurasel_text(note_text, rows_per_record=5):
    """テキストをクリーンアップし、指定行数ごとのリストに変換する"""

    # note_textを行ごとに分割して、空行と文字前後の空白を除去したリストを作成
    lines = [s for line in note_text.splitlines() if (s := line.strip())]

    # データの種類判定とヘッダ除去
    first_line = lines[0]
    if first_line not in ("収入の部", "支出の部"):
        raise ValueError("ヘッダの「収入の部」または「支出の部」の行からコピーしてください")

    data_kind = "収入" if first_line == "収入の部" else "支出"

    # 「合計行」が含まれていないかのチェック
    if any("合計" in line for line in lines):
        raise ValueError("「合計」の行は含めないでください")

    # 実データ部分の抽出（ヘッダ6要素をスキップ）
    core_data = lines[6:]

    # クリーンアップとグループ化
    record_list = []
    current_record = []
    for item in core_data:
        clean_item = item.replace("¥", "").replace("（円）", "").replace(",", "").strip()
        current_record.append(clean_item)
        if len(current_record) == rows_per_record:
            record_list.append(current_record)
            current_record = []

    return data_kind, record_list


def check_accountingclass(data_list, ac_name):
    """会計区分とデータ内容の整合性チェック
    - ac_nameの費目リストを作成
    - data_listの各要素の0番目（費目名）と比較
    """
    himoku_list = Himoku.get_himoku_list(ac_name)

    for d in data_list:
        if d[0] not in himoku_list:
            return False
    return True


def filter_community_himoku(data_list, ac_name):
    """管理組合会計の場合、町内会関連の費目を除外する"""
    if str(ac_name) == settings.COMMUNITY_ACCOUNTING:
        return data_list

    himoku_names = set(Himoku.get_without_community().values_list("himoku_name", flat=True))
    return [d for d in data_list if d[0] in himoku_names]


def execute_monthly_import(user, form_data):
    """
    インポート処理のメイン関数
    Returns: (success_bool, context_dict, error_messages)
    """
    year = form_data["year"]
    month = form_data["month"]
    ac_name = form_data["ac_class"]
    kind = form_data["kind"]
    mode = form_data["mode"]

    try:
        # 1. テキスト解析
        data_kind, data_list = translate_kurasel_text(form_data["note"])

        # 2. 収支区分バリデーション
        if data_kind != kind:
            return False, {}, ["「収支区分」がデータと一致していません！"]

        # 3. 会計区分整合性チェック
        if not check_accountingclass(data_list, str(ac_name)):
            return False, {}, ["「会計区分」を確認してください。"]

        # 4. 費目フィルタリング
        data_list = filter_community_himoku(data_list, ac_name)

        # 5. 合計計算
        total = sum(int(d[2]) for d in data_list)

        context_result = {
            "year": year,
            "month": month,
            "kind": kind,
            "mode": mode,
            "data_list": data_list,
            "total": total,
        }

        if "確認" in mode:
            return True, context_result, []

        # 6. 登録処理
        import_context = {**context_result, "author": user.pk}
        success, error_list = ReportTransaction.monthly_from_kurasel(ac_name, import_context)

        if success:
            # 相殺フラグ処理
            offset_himoku = ControlRecord.get_offset_himoku()
            if offset_himoku:
                tstart, tend = select_period(year, month)
                ReportTransaction.set_offset_flag(offset_himoku, tstart, tend)
            return True, context_result, []
        else:
            return False, context_result, [f"取り込み失敗: {e}" for e in error_list]

    except ValueError as e:
        return False, {}, [str(e)]
