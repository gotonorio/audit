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

                prev_dict, curr_dict = self.check_balancesheet(year, month, ac_class)
                context["difference"] = bank_balance - curr_dict["計算現金残高"]
                context["check_dict"] = curr_dict
                context["prev_dict"] = prev_dict
                context["curr_dict"] = curr_dict
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

    def check_balancesheet(self, year, month, ac_class):
        """町内会会計を含む貸借対照表のチェック（銀行残高の整合チェック）
        - 「未収金」「未払金」「前受金」「前払金」などの発生主義のズレ要素があるため、それらを調整して現金主義ベースに直す。
        - 今月末現金残高＝前月末現金残高+今月現金収入-今月現金支出-（前月未収金-今月未収金）+（前月未払金-今月未払金）+（前月前受金-今月前受金）-（前月前払金-今月前払金）
        - ただし、未収金、未払金がマイナスになる場合は、0とする。
        """
        # 会計区分毎の前月の資産
        previous_bs_dict = {}
        lastyear, lastmonth = get_lastmonth(year, month)
        last_tstart, last_tend = select_period(lastyear, lastmonth)
        # 会計区分毎の当月の資産
        current_bs_dict = {}
        tstart, tend = select_period(year, month)
        if ac_class > 0:
            # 前月末の貸借対照表データ（資産の部）を取得
            previous_qs_asset = BalanceSheet.get_bs(last_tstart, last_tend, ac_class, True).values_list(
                "item_name__item_name", "amounts", "comment"
            )
            # 前月末の貸借対照表データ（負債・剰余金の部）を取得
            previous_qs_debt = BalanceSheet.get_bs(last_tstart, last_tend, ac_class, False).values_list(
                "item_name__item_name", "amounts", "comment"
            )
            # 前月の貸借対照表データが存在しない場合
            if not previous_qs_asset:
                raise ValueError("前月の貸借対照表データが存在しません。")

            # （1）前月末の現金残高
            last_bankbalance = [row for row in previous_qs_asset if settings.BANK_NAME in row[0]]
            if not last_bankbalance:
                raise ValueError("前月の貸借対照表データに銀行残高が存在しません。")
            previous_bs_dict[settings.BANK_NAME] = last_bankbalance[0][1]
            # （2）前月の未収金
            last_recivable = [row for row in previous_qs_asset if settings.RECIVABLE in row[0]]
            if last_recivable:
                previous_bs_dict[settings.RECIVABLE] = last_recivable[0][1]
            else:
                previous_bs_dict[settings.RECIVABLE] = 0
            # （3）前月の未払金
            last_payable = [row for row in previous_qs_debt if settings.PAYABLE in row[0]]
            if last_payable:
                previous_bs_dict[settings.PAYABLE] = last_payable[0][1]
            else:
                previous_bs_dict[settings.PAYABLE] = 0
            # （4）前月の前受金
            last_maeuke = [row for row in previous_qs_debt if settings.MAEUKE in row[0]]
            if last_maeuke:
                previous_bs_dict[settings.MAEUKE] = last_maeuke[0][1]
            else:
                previous_bs_dict[settings.MAEUKE] = 0
            # （5）前月の前払金
            last_maebarai = [row for row in previous_qs_asset if settings.MAEBARAI in row[0]]
            if last_maebarai:
                previous_bs_dict[settings.MAEBARAI] = last_maebarai[0][1]
            else:
                previous_bs_dict[settings.MAEBARAI] = 0

            # 当月の貸借対照表データ（資産の部）を取得
            current_qs_asset = BalanceSheet.get_bs(tstart, tend, ac_class, True).values_list(
                "item_name__item_name", "amounts", "comment"
            )
            # 当月の貸借対照表データ（負債・剰余金の部）を取得
            current_qs_debt = BalanceSheet.get_bs(tstart, tend, ac_class, False).values_list(
                "item_name__item_name", "amounts", "comment"
            )
            # (6) 当月の収入合計（町内会費会計を除く）
            qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "income", False)
            # 当月収入合計
            current_income = ReportTransaction.total_calc_flg(qs)
            current_bs_dict["当月収入"] = current_income
            # (7) 当月の支出合計（口座振替手数料・町内会費会計を除く）
            qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "expense", False)
            # 当月支出合計
            current_expense = ReportTransaction.total_calc_flg(qs)
            current_bs_dict["当月支出"] = current_expense
            # (8) 当月の未収金
            current_recivable = [row for row in current_qs_asset if settings.RECIVABLE in row[0]]
            if current_recivable:
                current_bs_dict[settings.RECIVABLE] = current_recivable[0][1]
            else:
                current_bs_dict[settings.RECIVABLE] = 0
            # (9) 当月の未払金
            current_payable = [row for row in current_qs_debt if settings.PAYABLE in row[0]]
            if current_payable:
                current_bs_dict[settings.PAYABLE] = current_payable[0][1]
                logger.debug(f"check_bs_new: current_payable={current_payable[0][1]}")
            else:
                current_bs_dict[settings.PAYABLE] = 0
            # (10) 当月の前受金
            current_maeuke = [row for row in current_qs_debt if settings.MAEUKE in row[0]]
            if current_maeuke:
                current_bs_dict[settings.MAEUKE] = current_maeuke[0][1]
            else:
                current_bs_dict[settings.MAEUKE] = 0
            # (11) 当月の前払金
            current_maebarai = [row for row in current_qs_asset if settings.MAEBARAI in row[0]]
            if current_maebarai:
                current_bs_dict[settings.MAEBARAI] = current_maebarai[0][1]
            else:
                current_bs_dict[settings.MAEBARAI] = 0

            # 当月の現金残高
            calc_bankbalance = (
                previous_bs_dict[settings.BANK_NAME]
                + current_bs_dict["当月収入"]
                - current_bs_dict["当月支出"]
                - (current_bs_dict[settings.RECIVABLE] - previous_bs_dict[settings.RECIVABLE])
                + (current_bs_dict[settings.PAYABLE] - previous_bs_dict[settings.PAYABLE])
                + (current_bs_dict[settings.MAEUKE] - previous_bs_dict[settings.MAEUKE])
                - (current_bs_dict[settings.MAEBARAI] - previous_bs_dict[settings.MAEBARAI])
            )
            current_bs_dict["計算現金残高"] = calc_bankbalance

        return previous_bs_dict, current_bs_dict


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
