# views/balance_sheet_views.py
import logging

from django.conf import settings
from passbook.services import select_period

from monthly_report.forms import MonthlyReportViewForm
from monthly_report.models import BalanceSheet
from monthly_report.services.balance_sheet_check_service import check_balancesheet
from monthly_report.services.balance_sheet_service import (
    fetch_balancesheet_all,
    fetch_balancesheet_by_class,
    get_accounting_class_name,
    make_balancesheet,
    merge_balancesheet,
)

from .base import MonthlyReportBaseView

logger = logging.getLogger(__name__)


# =============================================================================
# 貸借対照表 表示 View
# =============================================================================
class BalanceSheetTableView(MonthlyReportBaseView):
    """
    貸借対照表の表示専用 View
    - 年・月・会計区分の取得は MonthlyReportBaseView に委譲
    - 会計計算・DB集計は service に委譲
    """

    template_name = "monthly_report/bs_table.html"
    permission_required = ("budget.view_expensebudget",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # パラメータ取得（base.view）
        year, month, ac_class = self.get_year_month_ac(kwargs)

        # 表示用 会計区分名（balance_sheet_service.py）
        ac_class_name = get_accounting_class_name(ac_class)

        # 対象期間の算出（passbook/services.py）
        tstart, tend = select_period(year, month)

        # 貸借対照表データ取得（next関数で銀行残高を取り出し、計算現金残高との差分を算出）
        if ac_class > 0:
            # 会計区分別に取得
            asset_list, debt_list = fetch_balancesheet_by_class(tstart, tend, ac_class)

            # 銀行残高チェック（存在する場合のみ）
            prev_dict, curr_dict = check_balancesheet(year, month, ac_class)
            if prev_dict and curr_dict:
                bank_balance = next(
                    (row[1] for row in asset_list if settings.BANK_NAME in row[0]),
                    0,
                )
                context["difference"] = bank_balance - curr_dict["計算現金残高"]
                context["prev_dict"] = prev_dict
                context["curr_dict"] = curr_dict
        else:
            # 全会計区分（町内会会計含む）取得
            asset_list, debt_list = fetch_balancesheet_all(tstart, tend)

        # 表構造の整形
        if not asset_list or not debt_list:
            # データなし（空画面）
            context.update(
                {
                    "form": self._build_form(year, month, ac_class),
                    "year": year,
                    "month": month,
                    "ac_class": ac_class,
                }
            )
            return context

        # 「負債の部」見出し
        debt_list.insert(0, ["--- 負債の部 ---", "", None])

        # 合計・剰余金行の生成
        asset_list, debt_list, total_bs = make_balancesheet(asset_list, debt_list)

        # 資産・負債を横並びに結合
        balance_list = merge_balancesheet(asset_list, debt_list, total_bs)

        # Context 設定
        context.update(
            {
                "title": self._build_title(year, month, ac_class_name),
                "bs_list": balance_list,
                "form": self._build_form(year, month, ac_class),
                "year": year,
                "month": month,
                "ac_class": ac_class,
            }
        )

        return context

    # -------------------------------------------------------------------------
    # private helper methods
    # -------------------------------------------------------------------------
    def _build_title(self, year, month, ac_class_name):
        """画面タイトルを返す"""
        period_no = year - settings.FIRST_PERIOD_YEAR + 1
        return f"第{period_no}期 {month}月 {ac_class_name}"

    def _build_form(self, year, month, ac_class):
        """メニューフォームを返す"""
        return MonthlyReportViewForm(
            initial={
                "year": year,
                "month": month,
                "accounting_class": ac_class,
            }
        )


# =============================================================================
# 貸借対照表 修正用一覧 View
# =============================================================================
class BalanceSheetListView(MonthlyReportBaseView):
    """
    貸借対照表 修正用リスト表示 View

    - Create / Update / Delete 画面への導線
    - 表示のみで計算ロジックは持たない
    """

    template_name = "monthly_report/bs_list.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # パラメータ取得
        year, month, ac_class = self.get_year_month_ac(kwargs)
        tstart, tend = select_period(year, month)

        qs = (
            BalanceSheet.objects.filter(monthly_date__range=[tstart, tend])
            .select_related("item_name", "item_name__ac_class")
            .order_by("monthly_date", "item_name__ac_class", "item_name__code")
        )

        if ac_class != 0:
            qs = qs.filter(item_name__ac_class=ac_class)

        context.update(
            {
                "bs_list": qs,
                "form": self._build_form(year, month, ac_class),
                "year": year,
                "month": month,
                "ac_class": ac_class,
            }
        )
        return context

    def _build_form(self, year, month, ac_class):
        return MonthlyReportViewForm(
            initial={
                "year": year,
                "month": month,
                "accounting_class": ac_class,
            }
        )
