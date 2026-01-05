# monthly_report/services/balance_sheet_services.py
import logging

from monthly_report.models import BalanceSheet
from passbook.services import append_list
from record.models import AccountingClass

logger = logging.getLogger(__name__)


def get_accounting_class_name(ac_class: int) -> str:
    """会計区分名を返す"""
    if ac_class == 0:
        return "合算会計（町内会費会計含む）"
    return AccountingClass.get_accountingclass_name(ac_class)


def fetch_balancesheet_by_class(tstart, tend, ac_class):
    """会計区分別の貸借対照表データ取得"""
    asset_qs = BalanceSheet.get_bs(tstart, tend, ac_class, True).values_list(
        "item_name__item_name", "amounts", "comment"
    )
    debt_qs = BalanceSheet.get_bs(tstart, tend, ac_class, False).values_list(
        "item_name__item_name", "amounts", "comment"
    )
    return [list(i) for i in list(asset_qs)], [list(i) for i in list(debt_qs)]


def fetch_balancesheet_all(tstart, tend):
    """全会計区分（町内会含む）の貸借対照表"""
    asset_list = []
    debt_list = []

    for item in BalanceSheet.get_bs(tstart, tend, ac_class=False, is_asset=True):
        tmp = list(item.values())
        tmp.append("")
        asset_list.append(tmp)

    for item in BalanceSheet.get_bs(tstart, tend, ac_class=False, is_asset=False):
        tmp = list(item.values())
        tmp.append("")
        debt_list.append(tmp)

    return asset_list, debt_list


def make_balancesheet(asset, debt):
    """貸借対照表の合計行を生成"""
    asset_total = sum(item[1] for item in asset)
    debt_total = sum(item[1] for item in debt if item[1] != "")

    debt.extend(
        [
            ["負債の部合計", debt_total, None],
            [" ", "", None],
            ["--- 剰余金の部 ---", "", None],
            ["剰余の部合計", asset_total - debt_total, None],
            [" ", "", None],
        ]
    )
    return asset, debt, asset_total


def merge_balancesheet(asset_list, debt_list, total_bs):
    """資産・負債を結合
    - 摘要は空欄で結合
    """
    balance_list = append_list(asset_list, debt_list, "")
    balance_list.append(
        [
            "資産の部合計",
            total_bs,
            None,
            "負債・剰余金の合計",
            total_bs,
            None,
        ]
    )
    return balance_list
