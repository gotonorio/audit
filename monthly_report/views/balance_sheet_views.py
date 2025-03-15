import logging

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from monthly_report.forms import MonthlyReportViewForm
from monthly_report.models import BalanceSheet, ReportTransaction
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
            ac_class = int(ac_class)
            ac_class_name = AccountingClass.get_accountingclass_name(ac_class)
        # 抽出期間
        tstart, tend = select_period(year, month)

        asset_list = []
        debt_list = []

        if ac_class > 0:
            # 会計区分毎の貸借対照表データを読み込む
            qs_asset = BalanceSheet.get_bs(tstart, tend, ac_class, True).values_list(
                "item_name__item_name", "amounts", "comment"
            )
            qs_debt = BalanceSheet.get_bs(tstart, tend, ac_class, False).values_list(
                "item_name__item_name", "amounts", "comment"
            )
            # querysetの結果で資産リストを作成。
            asset_list = [list(i) for i in list(qs_asset)]
            if asset_list:
                # 未収金
                recivable = [row for row in asset_list if settings.RECIVABLE in row[0]]
                if recivable:
                    recivable = recivable[0][1]
                else:
                    recivable = 0
                # 口座残高
                bank_balance = [row for row in asset_list if settings.BANK_NAME in row[0]]
                if bank_balance:
                    bank_balance = bank_balance[0][1]
                else:
                    bank_balance = 0

                # 貸借対照表データのチェック
                check_bs = self.check_balancesheet(year, month, ac_class, recivable)
                context["chk_lastbank"] = check_bs["前月の銀行残高"]
                context["chk_lastrecivable"] = check_bs["前月の未収金"]
                context["chk_income"] = check_bs["当月の収入"]
                context["chk_recivable"] = recivable
                context["chk_payable"] = check_bs["前月の未払金"]
                context["chk_expense"] = check_bs["当月の支出"]
                logger.debug(check_bs["前月の未払金"])
                context["chk_bank"] = (
                    check_bs["前月の銀行残高"]
                    + check_bs["前月の未収金"]
                    + check_bs["当月の収入"]
                    - check_bs["当月の支出"]
                    - recivable
                    - check_bs["前月の未払金"]
                )
                context["difference"] = bank_balance - context["chk_bank"]
            # querysetの結果で負債・剰余金リストを作成。
            debt_list = [list(i) for i in list(qs_debt)]
        else:
            # 全会計区分（町内会会計含む）の貸借対照表データを読み込む
            asset_list, debt_list = self.get_balancesheet(tstart, tend)

        debt_list.insert(0, ["--- 負債の部 ---", "", None])
        # 「負債の部合計」「剰余金の部合計」をasset_listに追加する。
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

    def make_balancesheet(self, asset, debt):
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

    def get_balancesheet(self, tstart, tend):
        """会計区分全体の貸借対照表（町内会会計を含む）データを返す"""
        asset_list = []
        debt_list = []
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

        return asset_list, debt_list

    def check_balancesheet(self, year, month, ac_class, recivable):
        """町内会会計を含む貸借対照表のチェック（銀行残高の整合）"""
        # 会計区分毎の前月の資産
        rtn_dict = {}
        lastyear, lastmonth = get_lastmonth(year, month)
        last_tstart, last_tend = select_period(lastyear, lastmonth)
        logger.debug(f"前月：{lastyear}-{lastmonth}")
        if ac_class > 0:
            # 会計区分を指定して貸借対照表を求める場合
            # 前月の未収金
            qs_asset = BalanceSheet.get_bs(last_tstart, last_tend, ac_class, True).values_list(
                "item_name__item_name", "amounts", "comment"
            )
            last_recivable = [row for row in qs_asset if settings.RECIVABLE in row[0]]
            if last_recivable:
                last_recivable = last_recivable[0][1]
            else:
                last_recivable = 0
            # 前月の未払金
            qs_debt = BalanceSheet.get_bs(last_tstart, last_tend, ac_class, False).values_list(
                "item_name__item_name", "amounts", "comment"
            )
            last_payable = [row for row in qs_debt if settings.PAYABLE in row[0]]
            if last_payable:
                last_payable = last_payable[0][1]
            else:
                last_payable = 0

            # 前月の銀行残高
            last_bankbalance = qs_asset[0][1]

            # 当月の収入合計（未収金含む）
            tstart, tend = select_period(year, month)
            qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "income", False)
            total_income = ReportTransaction.total_calc_flg(qs)
            # 当月の支出合計
            qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "expense", False)
            total_withdrawals = ReportTransaction.total_calc_flg(qs)
            # 当月の銀行残高（計算値）
            bank_balance = last_bankbalance + (total_income - total_withdrawals)
            # 当月の銀行残高（貸借対照表データ）
            rtn_dict["前月の銀行残高"] = last_bankbalance
            rtn_dict["前月の未収金"] = last_recivable
            rtn_dict["前月の未払金"] = last_payable
            rtn_dict["当月の収入"] = total_income
            rtn_dict["当月の支出"] = total_withdrawals
            rtn_dict["当月の銀行残高"] = bank_balance
        else:
            # 全会計区分の貸借対照表を求める場合
            asset_list, debt_list = self.get_balancesheet(last_tstart, last_tend)
            bank_balance = 0

        return rtn_dict


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
