import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from monthly_report.forms import MonthlyReportViewForm
from monthly_report.models import BalanceSheet
from passbook.utils import append_list, get_lastmonth, select_period
from record.models import AccountingClass

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# 貸借対照表表示用View
# -----------------------------------------------------------------------------
class BalanceSheetTableView(PermissionRequiredMixin, generic.TemplateView):
    """貸借対照表の表示"""

    permission_required = ("budget.view_expensebudget",)

    # templateファイルの切り替え
    def get_template_names(self):
        """templateファイルを切り替える"""
        if self.request.user_agent_flag == "mobile":
            template_name = "monthly_report/bs_table_mobile.html"
        else:
            template_name = "monthly_report/bs_table.html"
        return [template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # update後に元のviewに戻る。(get_success_url()のrevers_lazyで遷移する場合)
        if kwargs:
            # update後にget_success_url()で遷移する場合、kwargsにデータが渡される)
            year = kwargs.get("year")
            month = kwargs.get("month")
            ac_class = kwargs.get("ac_class")
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)
            ac_class = self.request.GET.get("accounting_class", 1)

        # 会計区分名(ac_class)
        # Noneならばdefault値だが、''の場合は、自分で処理しなければならない。
        if ac_class == "":
            ac_class_name = "合算会計（町内会費会計含む）"
            ac_class = 0
        else:
            ac_class_name = AccountingClass.get_accountingclass_name(ac_class)
        # 抽出期間
        tstart, tend = select_period(year, month)

        asset_list = []
        debt_list = []
        if ac_class == 0:
            # # 会計区分全体の貸借対照表（町内会会計を除く）
            # all_asset = BalanceSheet.get_bs(tstart, tend, False, True).exclude(
            #     item_name__ac_class__accounting_name=settings.COMMUNITY_ACCOUNTING
            # )
            all_asset = BalanceSheet.get_bs(tstart, tend, False, True)
            for item in all_asset:
                tmp_list = list(item.values())
                tmp_list.append("")
                asset_list.append(tmp_list)
            all_debt = BalanceSheet.get_bs(tstart, tend, False, False)
            for item in all_debt:
                tmp_list = list(item.values())
                tmp_list.append("")
                debt_list.append(tmp_list)
        else:
            # 会計区分毎の貸借対照表
            qs_asset = BalanceSheet.get_bs(tstart, tend, ac_class, True).values_list(
                "item_name__item_name", "amounts", "comment"
            )
            qs_debt = BalanceSheet.get_bs(tstart, tend, ac_class, False).values_list(
                "item_name__item_name", "amounts", "comment"
            )
            all_debt = BalanceSheet.get_bs(tstart, tend, ac_class, False)
            # querysetの結果で資産リストを作成。
            asset_list = [list(i) for i in list(qs_asset)]
            # querysetの結果で負債・剰余金リストを作成。
            debt_list = [list(i) for i in list(qs_debt)]

        debt_list.insert(0, ["--- 負債の部 ---", "", None])
        # 「負債の部合計」「剰余金の部合計」を追加する。
        asset_list, debt_list, total_bs = self.make_balancesheet(asset_list, debt_list)

        # forms.pyに初期値を設定する
        form = MonthlyReportViewForm(
            initial={
                "year": year,
                "month": month,
                "accounting_class": ac_class,
            }
        )

        # 資産リストと負債リストを合成する。
        if len(asset_list) > 0 and len(debt_list) > 0:
            balance_list = append_list(asset_list, debt_list, "")
            # 最後に「資産の部合計」と「負債・剰余金の合計」行を追加する。
            last_line = [
                "資産の部合計",
                total_bs,
                None,
                "負債・剰余金の合計",
                total_bs,
                None,
            ]
            balance_list.append(last_line)
        else:
            context["form"] = form
            context["year"] = year
            context["month"] = month
            context["ac_class"] = ac_class
            return context

        context["title"] = f"{year}年 {month}月 {ac_class_name}"
        context["bs_list"] = balance_list
        context["form"] = form
        context["year"] = year
        context["month"] = month
        context["ac_class"] = ac_class
        return context

    @staticmethod
    def make_balancesheet(asset, debt):
        """資産リストと負債リストから貸借対照表を生成する"""
        asset_total = 0
        debt_total = 0
        # 資産リストを作成
        for asset_item in asset:
            asset_total += asset_item[1]
        # 負債リストを作成
        for debt_item in debt:
            if debt_item[1] != "":
                debt_total += debt_item[1]
        debt.append(["負債の部合計", debt_total, None])
        debt.append([" ", "", None])
        debt.append(["--- 剰余金の部 ---", "", None])
        debt.append(["剰余の部合計", asset_total - debt_total, None])
        debt.append([" ", "", None])
        return asset, debt, asset_total

    @classmethod
    def check_balancesheet(year, month, ac_class):
        """貸借対照表のチェック
        - 銀行残高の整合
        - 未収金（滞納金一覧の合計金額）の整合
        - 前受金（前受金一覧の合計金額）の整合
        """
        # 前月の年月
        lastyear, lastmonth = get_lastmonth(year, month)
        # 前月の銀行残高
        last_bankbalance = 0


# -----------------------------------------------------------------------------
# 貸借対照表リスト表示用View
# -----------------------------------------------------------------------------
class BalanceSheetListView(PermissionRequiredMixin, generic.TemplateView):
    """貸借対照表の修正用リスト表示View"""

    template_name = "monthly_report/bs_list.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            # update後にget_success_url()で遷移する場合、kwargsにデータが渡される)
            year = kwargs.get("year")
            month = kwargs.get("month")
            ac_class = kwargs.get("ac_class", 1)
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)
            ac_class = self.request.GET.get("accounting_class", 0)
        # bs_table.htmlのリンクから飛んできた場合、 ac_class==""となる。
        if ac_class == "":
            ac_class = 0

        # 抽出期間
        tstart, tend = select_period(str(year), str(month))
        # 抽出期間の貸借対照表を抽出する。
        qs = BalanceSheet.objects.filter(monthly_date__range=[tstart, tend]).order_by(
            "monthly_date", "item_name__ac_class", "item_name__code"
        )
        if ac_class == 0:
            pass
        else:
            qs = qs.filter(item_name__ac_class=ac_class)

        # forms.pyのKeikakuListFormに初期値を設定する
        form = MonthlyReportViewForm(
            initial={
                "year": year,
                "month": month,
                "accounting_class": ac_class,
            }
        )
        context["bs_list"] = qs
        context["form"] = form
        context["year"] = year
        context["month"] = month
        context["ac_class"] = ac_class

        return context


# -----------------------------------------------------------------------------
# 貸借対照表チェックView
# -----------------------------------------------------------------------------
class BalanceSheetCheckView(PermissionRequiredMixin, generic.TemplateView):
    """"""
