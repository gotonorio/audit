# monthly_report/services/balance_sheet_check_service.py

import logging

from django.conf import settings
from monthly_report.models import BalanceSheet, ReportTransaction
from passbook.utils import get_lastmonth, select_period

logger = logging.getLogger(__name__)


def check_balancesheet(year, month, ac_class):
    """銀行残高整合チェック"""
    previous = {}
    current = {}

    # 「前月」と「当月」の日付範囲を取得
    lastyear, lastmonth = get_lastmonth(year, month)
    last_tstart, last_tend = select_period(lastyear, lastmonth)
    tstart, tend = select_period(year, month)

    # 「前月」の貸借対照表データ取得
    prev_asset = BalanceSheet.get_bs(last_tstart, last_tend, ac_class, True).values_list(
        "item_name__item_name", "amounts"
    )
    prev_debt = BalanceSheet.get_bs(last_tstart, last_tend, ac_class, False).values_list(
        "item_name__item_name", "amounts"
    )
    # 前月データが存在しない場合はチェック不可
    if not prev_asset:
        return None, None

    # 貸借対照表抽出querysetから「key」で指定した名称の値を取り出して返す。
    # 見つからない場合は 0 を返す。
    def pick(qs, key):
        return next((v for k, v in qs if key in k), 0)

    previous[settings.BANK_NAME] = pick(prev_asset, settings.BANK_NAME)
    previous[settings.RECIVABLE] = pick(prev_asset, settings.RECIVABLE)
    previous[settings.MAEBARAI] = pick(prev_asset, settings.MAEBARAI)
    previous[settings.PAYABLE] = pick(prev_debt, settings.PAYABLE)
    previous[settings.MAEUKE] = pick(prev_debt, settings.MAEUKE)

    income_qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "income", True)
    expense_qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "expense", True)

    current["当月収入"] = ReportTransaction.total_calc_flg(income_qs)
    current["当月支出"] = ReportTransaction.total_calc_flg(expense_qs)

    curr_asset = BalanceSheet.get_bs(tstart, tend, ac_class, True).values_list(
        "item_name__item_name", "amounts"
    )
    curr_debt = BalanceSheet.get_bs(tstart, tend, ac_class, False).values_list(
        "item_name__item_name", "amounts"
    )

    current[settings.RECIVABLE] = pick(curr_asset, settings.RECIVABLE)
    current[settings.MAEBARAI] = pick(curr_asset, settings.MAEBARAI)
    current[settings.PAYABLE] = pick(curr_debt, settings.PAYABLE)
    current[settings.MAEUKE] = pick(curr_debt, settings.MAEUKE)

    current["計算現金残高"] = (
        previous[settings.BANK_NAME]
        + current["当月収入"]
        - current["当月支出"]
        - (current[settings.RECIVABLE] - previous[settings.RECIVABLE])
        + (current[settings.PAYABLE] - previous[settings.PAYABLE])
        + (current[settings.MAEUKE] - previous[settings.MAEUKE])
        - (current[settings.MAEBARAI] - previous[settings.MAEBARAI])
    )

    return previous, current
