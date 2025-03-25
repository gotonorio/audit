import calendar
import logging

from control.models import ControlRecord
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.aggregates import Case, Sum, When
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from monthly_report.forms import MonthlyReportViewForm
from monthly_report.models import ReportTransaction
from passbook.utils import select_period
from record.models import AccountingClass

logger = logging.getLogger(__name__)


def monthly_total(qs, year, item_name):
    """指定された1年間の月毎の集計関数
    - 与えられたquerysetからitem_name項目の合計をDictで返す。
    - aggregateでの集約合計の結果がNoneの場合にデフォルトの0を返すためにCoalwsce()を使う。
    """
    rtn = {}
    for month in range(1, 13):
        day = calendar.monthrange(year, month)[1]
        sdate = timezone.datetime(year, month, 1, 0, 0, 0)
        edate = timezone.datetime(year, month, day, 0, 0, 0)
        rtn["total" + str(month)] = qs.filter(transaction_date__range=[sdate, edate]).aggregate(
            tmp=Coalesce(Sum(item_name), 0)
        )["tmp"]
    return rtn


def adjust_month(year, month):
    # 管理会社の月次報告は2ヶ月遅れ。
    if month == 0:
        mm = localtime(timezone.now()).month
        if mm == 1:
            year = year - 1
            month = 11
        elif mm == 2:
            year = year - 1
            month = 12
        else:
            month = str(mm - settings.DELAY_MONTH).zfill(2)
    return year, month


def get_year_period(year):
    """指定年の1年分の月範囲データをlistで返す"""
    period = []
    for month in range(1, 13):
        month_period = [0, 0]
        day = calendar.monthrange(year, month)[1]
        month_period[0] = timezone.datetime(year, month, 1, 0, 0, 0)
        month_period[1] = timezone.datetime(year, month, day, 0, 0, 0)
        period.append(month_period)
    return period


def get_allmonths_data(qs, year):
    """年間の月毎、費目毎金額の集計"""
    # 日付の期間を作成
    period = get_year_period(int(year))

    rtn = qs.values("himoku__himoku_name", "himoku__accounting_class__accounting_name").annotate(
        month1=Sum(
            Case(
                When(
                    transaction_date__range=[period[0][0], period[0][1]],
                    then="amount",
                ),
                default=0,
            )
        ),
        month2=Sum(
            Case(
                When(
                    transaction_date__range=[period[1][0], period[1][1]],
                    then="amount",
                ),
                default=0,
            )
        ),
        month3=Sum(
            Case(
                When(
                    transaction_date__range=[period[2][0], period[2][1]],
                    then="amount",
                ),
                default=0,
            )
        ),
        month4=Sum(
            Case(
                When(
                    transaction_date__range=[period[3][0], period[3][1]],
                    then="amount",
                ),
                default=0,
            )
        ),
        month5=Sum(
            Case(
                When(
                    transaction_date__range=[period[4][0], period[4][1]],
                    then="amount",
                ),
                default=0,
            )
        ),
        month6=Sum(
            Case(
                When(
                    transaction_date__range=[period[5][0], period[5][1]],
                    then="amount",
                ),
                default=0,
            )
        ),
        month7=Sum(
            Case(
                When(
                    transaction_date__range=[period[6][0], period[6][1]],
                    then="amount",
                ),
                default=0,
            )
        ),
        month8=Sum(
            Case(
                When(
                    transaction_date__range=[period[7][0], period[7][1]],
                    then="amount",
                ),
                default=0,
            )
        ),
        month9=Sum(
            Case(
                When(
                    transaction_date__range=[period[8][0], period[8][1]],
                    then="amount",
                ),
                default=0,
            )
        ),
        month10=Sum(
            Case(
                When(
                    transaction_date__range=[period[9][0], period[9][1]],
                    then="amount",
                ),
                default=0,
            )
        ),
        month11=Sum(
            Case(
                When(
                    transaction_date__range=[period[10][0], period[10][1]],
                    then="amount",
                ),
                default=0,
            )
        ),
        month12=Sum(
            Case(
                When(
                    transaction_date__range=[period[11][0], period[11][1]],
                    then="amount",
                ),
                default=0,
            )
        ),
        # 12ヶ月分の合計
        total=Sum(
            Case(
                When(
                    transaction_date__range=[period[0][0], period[11][1]],
                    then="amount",
                ),
                default=0,
            )
        ),
    )
    return rtn.order_by("himoku__accounting_class__code", "himoku__code")


def aggregate_himoku(qs):
    """querysetデータを費目で集計してdictで返す"""
    pb_dict = {}
    for item in qs:
        key = item.himoku.himoku_name
        if key in pb_dict:
            pb_dict[key] = pb_dict[key] + item.amount
        else:
            pb_dict[key] = item.amount
    return pb_dict


def qs_year_income(tstart, tend, ac_class, others_flg):
    """月次報告の年間収入データを返す
    settings.COMMUNITY_FLAG:町内会会計を含むかどうかのフラグ
    """
    # 月次報告収入リスト
    qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "income", settings.COMMUNITY_FLAG)
    # 修繕積立会計の「修繕積立金」以外の収入を抽出する。
    if others_flg:
        qs = qs.exclude(himoku__himoku_name="修繕積立金")
    # 月次報告収入の月別合計を計算。
    year = tstart.year
    mr_total = monthly_total(qs, int(year), "amount")
    # 年間合計を計算してmr_totalに追加する。
    mr_total["year_total"] = sum(mr_total.values())
    # 各月毎の収入額を抽出。
    qs = get_allmonths_data(qs, year)
    return qs, mr_total


class MonthlyReportExpenseListView(PermissionRequiredMixin, generic.TemplateView):
    """月次報告 支出リスト"""

    template_name = "monthly_report/monthly_report_expense.html"
    permission_required = ("budget.view_expensebudget",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            # update後にget_success_url()で遷移する場合、kwargsにデータが渡される。typeはint)
            year = str(kwargs.get("year"))
            month = str(kwargs.get("month"))
            ac_class = str(kwargs.get("ac_class"))
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
        ac_name = AccountingClass.get_accountingclass_obj(AccountingClass.get_class_name("町内"))
        if ac_name.pk == int(ac_class):
            # 町内会会計が指定された場合。
            qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "expense", True)
        else:
            # 町内会会計以外が指定された場合。
            qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "expense", False)
        # 表示順序
        qs = qs.order_by(
            "himoku__accounting_class",
            "himoku__code",
            "calc_flg",
            "transaction_date",
        )
        # 合計金額（計算対象のみ）
        total_withdrawals = ReportTransaction.total_calc_flg(qs)
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
            year = kwargs.get("year")
            month = kwargs.get("month")
            ac_class = str(kwargs.get("ac_class"))
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
        else:
            # 町内会会計以外が指定された場合。
            qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "income", False)
        # 月次データの収入合計
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
            year = str(kwargs.get("year"))
            ac_class = str(kwargs.get("ac_class"))
        else:
            # formで戻った場合、requestからデータを取り出す。（typeはstr、ALLは""となる）
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            ac_class = self.request.GET.get("accounting_class", "0")
            # ac_classが「空」の場合の処理
            if ac_class == "":
                ac_class = "0"

        # 抽出期間
        tstart, tend = select_period(year, 0)

        qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "expense", settings.COMMUNITY_FLAG)
        # 月次報告支出の月別合計を計算。 aggregateは辞書を返す。
        mr_total = monthly_total(qs, int(year), "amount")
        # 年間合計を計算してmr_totalに追加する。
        mr_total["year_total"] = sum(mr_total.values())

        context["mr_total"] = mr_total
        # 各月毎の支出額を抽出。行集約は最後に行う必要がある。
        qs = get_allmonths_data(qs, year)
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
            year = str(kwargs.get("year"))
            ac_class = str(kwargs.get("ac_class"))
        else:
            # formで戻った場合、requestからデータを取り出す。（typeはstr、ALLは""となる）
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            ac_class = self.request.GET.get("accounting_class", "0")
            # ac_classが「空」の場合の処理
            if ac_class == "":
                ac_class = "0"

        # 抽出期間（monthが"all"なら1年分）
        tstart, tend = select_period(year, 0)
        qs, mr_total = qs_year_income(tstart, tend, ac_class, False)
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
            year = str(kwargs.get("year"))
            ac_class = str(kwargs.get("ac_class"))
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
        mr_income_total = monthly_total(qs_income, int(year), "amount")
        # 年間合計を計算してmr_income_totalに追加する。
        mr_income_total["income_year_total"] = sum(mr_income_total.values())
        context["mr_income_total"] = mr_income_total

        # 支出
        qs_expense = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "expense", False)
        # 月次報告支出の月別合計を計算。 aggregateは辞書を返す。
        mr_expense_total = monthly_total(qs_expense, int(year), "amount")
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


class CalcFlgCheckList(PermissionRequiredMixin, generic.TemplateView):
    """合計計算から除外している項目リスト
    - calc_flg（計算対象フラグ）がFalse
    - 細目レベルでis_aggregareがFalse
    """

    template_name = "monthly_report/calcflg_check_list.html"
    permission_required = "record.add_transaction"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.GET.get("year", localtime(timezone.now()).year)
        # 抽出期間
        tstart, tend = select_period(year, 0)
        # 合計計算除外項目リスト（calc_flg=False, aggregate_flag=False）
        qs = ReportTransaction.get_calcflg_check(tstart, tend)
        # 除外項目の合計
        total = 0
        for i in qs:
            total += i.amount
        # formに初期値を設定する
        form = MonthlyReportViewForm(
            initial={
                "year": year,
            }
        )
        context["calcflg_off_list"] = qs
        context["total"] = total
        context["form"] = form
        context["year"] = year
        return context


class CheckOffset(PermissionRequiredMixin, generic.TemplateView):
    """「口座振替手数料」の相殺処理のフラグをチェック"""

    template_name = "monthly_report/chk_offset.html"
    permission_required = "record.add_transaction"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.GET.get("year", localtime(timezone.now()).year)
        # 抽出期間
        tstart, tend = select_period(year, 0)
        # 費目名「口座振替手数料」でfilter
        offset_himoku_name = ControlRecord.get_offset_himoku()
        if offset_himoku_name is None:
            messages.info(self.request, "相殺処理する費目が設定されていません。")
        # 期間と相殺処理する費目名でfiler
        qs = (
            ReportTransaction.objects.all()
            .filter(transaction_date__range=[tstart, tend])
            .filter(himoku__himoku_name=offset_himoku_name)
            .order_by("-transaction_date")
        )
        form = MonthlyReportViewForm(
            initial={
                "year": year,
            }
        )
        context["chk_obj"] = qs
        context["form"] = form
        return context


class UnpaidBalanceListView(PermissionRequiredMixin, generic.TemplateView):
    """未払金一覧"""

    template_name = "monthly_report/unpaid_list.html"
    permission_required = "record.add_transaction"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.GET.get("year", localtime(timezone.now()).year)
        # 抽出期間
        tstart, tend = select_period(year, 0)
        # 未払金リスト
        qs = ReportTransaction.get_unpaid_balance(tstart, tend)
        # 未払金の合計
        total = 0
        for i in qs:
            total += i.amount
        # formに初期値を設定する
        form = MonthlyReportViewForm(
            initial={
                "year": year,
            }
        )
        context["unpaid_list"] = qs
        context["total"] = total
        context["form"] = form
        context["year"] = year
        return context


class SimulatonDataListView(PermissionRequiredMixin, generic.TemplateView):
    """長期修繕計画シミュレーション用データリスト
    - 長期修繕計画シミュレーション用データとして、修繕積立金会計と駐車場会計の実績収入リストを表示する。
    """

    template_name = "monthly_report/simulation_data.html"
    permission_required = ("record.add_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            # 年間収入画面から遷移した場合、kwargsにデータが渡される。(typeはint)
            year = str(kwargs.get("year"))
        else:
            # formで戻った場合、requestからデータを取り出す。（typeはstr、ALLは""となる）
            year = self.request.GET.get("year", localtime(timezone.now()).year)

        # 抽出期間（年間）
        tstart, tend = select_period(year, 0)
        # 修繕積立金会計クラスID
        ac_shuuzen = AccountingClass.objects.get(accounting_name="修繕積立金会計")
        ac_parking = AccountingClass.objects.get(accounting_name="駐車場会計")

        # 修繕積立金会計「その他収入」リスト
        qs_others_income, others_income_total = qs_year_income(tstart, tend, ac_shuuzen, True)
        context["others_income_total"] = others_income_total

        # 駐車場会計
        qs_parking, parking_total = qs_year_income(tstart, tend, ac_parking, False)
        context["parking_total"] = parking_total

        # form 初期値を設定
        form = MonthlyReportViewForm(
            initial={
                "year": year,
            }
        )
        context["others_income_list"] = qs_others_income
        context["parking_income_list"] = qs_parking
        context["form"] = form
        context["yyyymm"] = str(year) + "年"
        context["year"] = year
        return context
