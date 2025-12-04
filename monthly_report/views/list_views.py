import logging

from control.models import ControlRecord
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from monthly_report.forms import MonthlyReportViewForm
from monthly_report.models import ReportTransaction
from monthly_report.services import monthly_report_services
from passbook.utils import select_period
from record.models import AccountingClass

logger = logging.getLogger(__name__)


class MonthlyReportExpenseListView(PermissionRequiredMixin, generic.TemplateView):
    """月次報告 支出リスト"""

    template_name = "monthly_report/monthly_report_expense.html"
    permission_required = ("budget.view_expensebudget",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            # update後にget_success_url()で遷移する場合、kwargsにデータが渡される。typeはint)
            year = str(self.kwargs.get("year"))
            month = str(self.kwargs.get("month"))
            ac_class = str(self.kwargs.get("ac_class"))
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)
            ac_class = self.request.GET.get("accounting_class", "0")
            # ac_classが「空」の場合の処理
            if ac_class == "":
                ac_class = "0"

        # 抽出期間
        tstart, tend = select_period(year, month)

        # 町内会会計が選択された場合の処理
        ac_name = AccountingClass.get_accountingclass_obj(AccountingClass.get_class_name("町内会"))
        if ac_name.pk == int(ac_class):
            # 町内会会計が指定された場合。
            qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "expense", True)
            total_withdrawals = ReportTransaction.total_calc_flg(qs)
        else:
            # 全会計区分が選択された場合、町内会会計は除外する。
            qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "expense", False)
            total_withdrawals = ReportTransaction.total_calc_flg(qs)

        # 表示順序
        qs = qs.order_by(
            "himoku__accounting_class",
            "himoku__code",
            "calc_flg",
            "transaction_date",
        )
        # forms.pyのKeikakuListFormに初期値を設定する
        form = MonthlyReportViewForm(
            initial={
                "year": year,
                "month": month,
                "accounting_class": ac_class,
            }
        )
        context["transaction_list"] = qs
        context["form"] = form
        context["total_withdrawals"] = total_withdrawals
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["year"] = year
        context["month"] = month
        context["delete_flg"] = ControlRecord.get_delete_flg()
        # 会計区分が''だった場合の処理
        if ac_class == "":
            ac_class = "0"
        context["ac"] = ac_class

        return context


class MonthlyReportIncomeListView(PermissionRequiredMixin, generic.TemplateView):
    """月次報告 収入リスト"""

    template_name = "monthly_report/monthly_report_income.html"
    permission_required = ("budget.view_expensebudget",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            # update後にget_success_url()で遷移する場合、kwargsにデータが渡される。typeはint)
            year = self.kwargs.get("year")
            month = self.kwargs.get("month")
            ac_class = str(self.kwargs.get("ac_class"))
        else:
            # formで戻った場合、requestからデータを取り出す。（typeはstr、ALLは""となる）
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)
            ac_class = self.request.GET.get("accounting_class", "0")
            # ac_classが「空」の場合の処理
            if ac_class == "":
                ac_class = "0"
        # 抽出期間
        tstart, tend = select_period(year, month)
        # 町内会会計が選択された場合の処理
        ac_name = AccountingClass.get_accountingclass_obj(AccountingClass.get_class_name("町内"))
        if ac_name.pk == int(ac_class):
            # 町内会会計が指定された場合。
            qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "income", True)
            total_income = ReportTransaction.total_calc_flg(qs)
        else:
            # 全会計区分が選択された場合、町内会会計は除外する。
            qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "income", False)
            total_income = ReportTransaction.total_calc_flg(qs)

        # 表示順序
        qs = qs.order_by("himoku__accounting_class", "calc_flg", "transaction_date")
        # forms.pyのKeikakuListFormに初期値を設定する
        form = MonthlyReportViewForm(
            initial={
                "year": year,
                "month": month,
                "accounting_class": ac_class,
            }
        )
        context["transaction_list"] = qs
        context["form"] = form
        context["total_withdrawals"] = total_income
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["year"] = year
        context["month"] = month
        context["delete_flg"] = ControlRecord.get_delete_flg()
        # 会計区分が''だった場合の処理
        if ac_class == "":
            ac_class = "0"
        context["ac"] = ac_class

        return context


class YearExpenseListView(PermissionRequiredMixin, generic.TemplateView):
    """月次報告支出リスト 年間表示"""

    template_name = "monthly_report/year_expenselist.html"
    permission_required = ("budget.view_expensebudget",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            # 年間収入画面から遷移した場合、kwargsにデータが渡される。(typeはint)
            year = str(self.kwargs.get("year"))
            ac_class = str(self.kwargs.get("ac_class"))
        else:
            # formで戻った場合、requestからデータを取り出す。（typeはstr、ALLは""となる）
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            ac_class = self.request.GET.get("accounting_class", "0")
            # ac_classが「空」の場合の処理
            if ac_class == "":
                ac_class = "0"

        # 抽出期間
        tstart, tend = select_period(year, 0)

        qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "expense", True)
        # 月次報告支出の月別合計を計算。 aggregateは辞書を返す。
        mr_total = monthly_report_services.monthly_total(qs, int(year), "amount")
        # 年間合計を計算してmr_totalに追加する。
        mr_total["year_total"] = sum(mr_total.values())

        context["mr_total"] = mr_total
        # 各月毎の支出額を抽出。行集約は最後に行う必要がある。
        qs = monthly_report_services.get_allmonths_data(qs, year)
        # form 初期値を設定
        form = MonthlyReportViewForm(
            initial={
                "year": year,
                "accounting_class": ac_class,
            }
        )
        context["transaction_list"] = qs
        context["form"] = form
        context["yyyymm"] = str(year) + "年"
        context["year"] = year
        # 会計区分が''だった場合の処理
        if ac_class == "":
            ac_class = "0"
        context["ac"] = ac_class
        return context


class YearIncomeListView(PermissionRequiredMixin, generic.TemplateView):
    """月次報告収入リスト 年間表示"""

    template_name = "monthly_report/year_incomelist.html"
    permission_required = ("budget.view_expensebudget",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            # 年間収入画面から遷移した場合、kwargsにデータが渡される。(typeはint)
            year = str(self.kwargs.get("year"))
            ac_class = str(self.kwargs.get("ac_class"))
        else:
            # formで戻った場合、requestからデータを取り出す。（typeはstr、ALLは""となる）
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            ac_class = self.request.GET.get("accounting_class", "0")
            # ac_classが「空」の場合の処理
            if ac_class == "":
                ac_class = "0"

        # 抽出期間（monthが"all"なら1年分）
        tstart, tend = select_period(year, 0)
        qs, mr_total = monthly_report_services.qs_year_income(tstart, tend, ac_class, False)
        context["mr_total"] = mr_total

        # form 初期値を設定
        form = MonthlyReportViewForm(
            initial={
                "year": year,
                "accounting_class": ac_class,
            }
        )
        context["transaction_list"] = qs
        context["form"] = form
        context["yyyymm"] = str(year) + "年"
        context["year"] = year
        # 会計区分が''だった場合の処理
        if ac_class == "":
            ac_class = "0"
        context["ac"] = ac_class
        return context


class YearIncomeExpenseListView(PermissionRequiredMixin, generic.TemplateView):
    """収支リスト 年間表示"""

    template_name = "monthly_report/year_income_expenselist.html"
    permission_required = ("budget.view_expensebudget",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            # 年間収入画面から遷移した場合、kwargsにデータが渡される。(typeはint)
            year = str(self.kwargs.get("year"))
            ac_class = str(self.kwargs.get("ac_class"))
        else:
            # formで戻った場合、requestからデータを取り出す。（typeはstr、ALLは""となる）
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            ac_class = self.request.GET.get("accounting_class", "0")
            # ac_classが「空」の場合の処理
            if ac_class == "":
                ac_class = "0"

        # 抽出期間（monthが"all"なら1年分）
        tstart, tend = select_period(year, 0)

        # 収入
        qs_income = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "income", False)
        # 月次報告収入の月別合計を計算。
        mr_income_total = monthly_report_services.monthly_total(qs_income, int(year), "amount")
        # 年間合計を計算してmr_income_totalに追加する。
        mr_income_total["income_year_total"] = sum(mr_income_total.values())
        context["mr_income_total"] = mr_income_total

        # 支出
        qs_expense = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "expense", False)
        # 月次報告支出の月別合計を計算。 aggregateは辞書を返す。
        mr_expense_total = monthly_report_services.monthly_total(qs_expense, int(year), "amount")
        # 年間合計を計算してmr_totalに追加する。
        mr_expense_total["expense_year_total"] = sum(mr_expense_total.values())
        context["mr_expense_total"] = mr_expense_total

        # form 初期値を設定
        form = MonthlyReportViewForm(
            initial={
                "year": year,
                "accounting_class": ac_class,
            }
        )
        context["form"] = form
        context["year"] = year
        # 会計区分が''だった場合の処理
        if ac_class == "":
            ac_class = "0"
        context["ac"] = ac_class
        return context
