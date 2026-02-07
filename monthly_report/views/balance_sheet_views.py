# views/balance_sheet_views.py
import logging

from common.services import select_period
from control.models import FiscalLock
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.timezone import localtime
from django.views.generic import CreateView, DeleteView, FormView, UpdateView

from monthly_report.forms import (
    BalanceSheetForm,
    BalanceSheetItemForm,
    DeleteByYearMonthAcclass,
    MonthlyReportViewForm,
)
from monthly_report.models import BalanceSheet, BalanceSheetItem
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
                "ac_class": ac_class,
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
                "ac_class": ac_class,
            }
        )


# =============================================================================
# 貸借対照表 Create / Update / Delete Views
# =============================================================================
class BalanceSheetCreateView(PermissionRequiredMixin, CreateView):
    """貸借対照表の未収金・前受金・未払金のCreateView"""

    model = BalanceSheet
    form_class = BalanceSheetForm
    template_name = "monthly_report/bs_form.html"
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("monthly_report:create_bs")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = localtime(timezone.now()).year
        context["bs_list"] = BalanceSheet.objects.filter(monthly_date__contains=year).order_by(
            "-monthly_date", "item_name"
        )
        return context


class BalanceSheetUpdateView(PermissionRequiredMixin, UpdateView):
    """貸借対照表の未収金・前受金・未払金のUpdateView"""

    model = BalanceSheet
    form_class = BalanceSheetForm
    template_name = "monthly_report/bs_form.html"
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True

    # 保存が成功した場合に遷移するurl
    def get_success_url(self):
        """保存成功後、GETパラメータを付与した一覧画面へリダイレクト"""
        base_url = reverse("monthly_report:bs_table")
        # クエリパラメータを辞書形式で定義
        params = urlencode(
            {
                "year": self.object.monthly_date.year,
                "month": self.object.monthly_date.month,
                "ac_class": self.object.item_name.ac_class.pk,
            }
        )

        return f"{base_url}?{params}"


class BalanceSheetDeleteView(PermissionRequiredMixin, DeleteView):
    """貸借対照表データの削除処理"""

    model = BalanceSheet
    template_name = "monthly_report/bs_delete_confirm.html"
    permission_required = "record.add_transaction"
    success_url = reverse_lazy("monthly_report:create_bs")


class BalanceSheetItemCreateView(PermissionRequiredMixin, CreateView):
    """貸借対照表の科目データの作成"""

    model = BalanceSheetItem
    form_class = BalanceSheetItemForm
    template_name = "monthly_report/bs_item_form.html"
    permission_required = "record.add_transaction"
    raise_exception = True
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("monthly_report:create_bs_item")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bs_item_list"] = BalanceSheetItem.objects.all().order_by("code", "is_asset")
        return context


class BalanceSheetItemUpdateView(PermissionRequiredMixin, UpdateView):
    """貸借対照表の科目データのアップデート"""

    model = BalanceSheetItem
    form_class = BalanceSheetItemForm
    template_name = "monthly_report/bs_item_form.html"
    permission_required = "record.add_transaction"
    raise_exception = True
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("monthly_report:create_bs_item")


class BalanceSheetDeleteByYearMonthView(PermissionRequiredMixin, FormView):
    """指定された年月の支払いデータを一括削除するFormView
    - 決算完了年のデータは削除不可とする。
    """

    template_name = "monthly_report/bs_delete_by_yearmonth.html"
    form_class = DeleteByYearMonthAcclass
    return_base_url = "payment:payment_list"
    permission_required = "record.add_transaction"

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            year = form.cleaned_data["year"]
            month = form.cleaned_data["month"]
            ac_class = form.cleaned_data["ac_class"]

            # 判定：決算・月次締めチェック
            is_frozen = FiscalLock.is_period_frozen(int(year), int(month))
            # 決算完了のチェック
            if is_frozen:
                messages.error(request, f"{year}年{month}月は既に締められているため削除できません。")
                # form入力画面に戻す。redirectせず、今のform（入力値入り）を持ったまま入力画面を再表示する
                return self.render_to_response(self.get_context_data(form=form))

            # 「実行ボタン」が押された場合のみ削除
            if "execute_delete" in request.POST:
                count = BalanceSheet.delete_by_yearmonth(year, month, ac_class)
                messages.success(request, f"{year}年{month}月のデータを {count} 件削除しました。")

                # 削除後の戻り処理
                base_url = reverse(self.return_base_url)
                # クエリパラメータを辞書形式で定義
                params = urlencode(
                    {
                        "year": year,
                        "month": month,
                    }
                )
                return redirect(f"{base_url}?{params}")

            # 「確認ボタン」が押された場合は、データを抽出して同じページを表示
            target_data = BalanceSheet.objects.filter(monthly_date__year=year, monthly_date__month=month)
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    target_data=target_data,
                    confirm_mode=True,  # 確認モードフラグ
                    year=year,
                    month=month,
                )
            )
        return self.form_invalid(form)
