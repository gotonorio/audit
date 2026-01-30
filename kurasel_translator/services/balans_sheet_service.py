import logging

from monthly_report.models import BalanceSheet

from .common_service import clean_amount_str, clean_kurasel_text

logger = logging.getLogger(__name__)


def list_to_dict(data_list):
    """[key1, value1, key2, value2...] を辞書に変換"""
    bs_dict = {}
    for i in range(0, len(data_list) & ~1, 2):  # 要素が奇数の場合も考慮
        bs_dict[data_list[i]] = data_list[i + 1]
    return bs_dict


def parse_bs_text(msg_list):
    """
    テキストリストを解析して、会計区分名とBSデータ辞書を返す
    """
    if not msg_list:
        raise ValueError("データが空です。")

    # 1行目は会計区分名
    ac_class_name = msg_list.pop(0)
    if ac_class_name not in ("管理費会計", "修繕積立金会計", "駐車場会計", "町内会費会計"):
        raise ValueError("タイトルの「会計区分名」から「剰余の部合計」までをコピーしてください")

    asset_list = []
    debt_list = []
    is_asset_section = True

    for line in msg_list:
        clean_line = clean_amount_str(line)

        if clean_line == "資産の部":
            continue
        if clean_line in ["負債・剰余金の部", "負債の部"]:
            is_asset_section = False
            continue
        if clean_line == "負債の部合計":  # 取り込み終了の合図
            break

        if is_asset_section:
            asset_list.append(clean_line)
        else:
            debt_list.append(clean_line)

    # 辞書化して結合
    bs_dict = {**list_to_dict(asset_list), **list_to_dict(debt_list)}
    return ac_class_name, bs_dict


def execute_bs_import(user, form_data):
    """
    BalansSheetデータ取り込みのメイン実行関数
    Returns: (success_bool, result_context, error_messages)
    """
    year = form_data["year"]
    month = form_data["month"]
    # accounting_class = form_data["accounting_class"]
    ac_class = form_data["ac_class"]
    mode = form_data["mode"]

    try:
        # 1. 解析
        msg_list = clean_kurasel_text(form_data["note"])
        ac_class_name, bs_dict = parse_bs_text(msg_list)

        # 2. バリデーション（会計区分の不一致チェック）
        if str(ac_class) != ac_class_name:
            return (
                False,
                {},
                [f"選択された会計区分({ac_class})とデータ({ac_class_name})が一致しません。"],
            )

        result_context = {
            "year": year,
            "month": month,
            "ac_class": ac_class,
            "bs_dict": bs_dict,
            "author": user.pk,
            "mode": mode,
        }

        if "確認" in mode:
            return True, result_context, []

        # 3. 保存実行
        success, error_list = BalanceSheet.bs_from_kurasel(ac_class, result_context)
        if success:
            return True, result_context, []
        else:
            return False, result_context, [f"保存失敗: {e}" for e in error_list]

    except (ValueError, Exception) as e:
        return False, {}, [str(e)]
