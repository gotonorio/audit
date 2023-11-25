import calendar
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.aggregates import Max, Sum
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.generic import TemplateView

from budget.forms import Budget_listForm
from budget.models import ExpenseBudget
from monthly_report.models import ReportTransaction
from record.models import AccountingClass, Transaction

logger = logging.getLogger(__name__)


def composit(budget, expense):
    """予算と累積支出をlistで返す
    - 年次予算の費目で集計する。
    - 実際に支出した項目（費目）が抜けるため使用しない。
    """
    comp_list = []
    for d in budget:
        data = ["", "", 0, 0, 0, 0, ""]
        budget_himoku_id = d.himoku.id
        data[1] = d.himoku
        data[2] = d.budget_expense
        data[6] = d.comment
        for e in expense:
            if e["himoku"] == budget_himoku_id:
                data[3] = e["ruiseki"]
                data[4] = data[2] - data[3]
                if data[2] == 0:
                    data[5] = 0
                else:
                    data[5] = data[3] * 100 / data[2]
                break
        comp_list.append(data)
    return comp_list


def check_budget(budget, expense):
    """予算外データを返す"""
    comp_list = []
    for ex in expense:
        chk = False
        himoku_id = ex["himoku"]
        for bu in budget:
            if himoku_id == bu.himoku.id:
                chk = True
                break
        if chk:
            continue
        else:
            data = ["", "", 0, 0]
            data[0] = ex["himoku__accounting_class__accounting_name"]
            data[1] = ex["himoku__himoku_name"]
            data[2] = ex["ruiseki"]

        comp_list.append(data)
    return comp_list


def get_total(data_list):
    """表示されたデータでの合計を返す"""
    total_budget = 0
    total_ruikei = 0
    for data in data_list:
        total_budget += int(data[2])
        total_ruikei += int(data[3])
    return total_budget, total_ruikei


def near_month(qs):
    """月次報告の最新月を返す"""
    qs_month = qs.aggregate(Max("transaction_date"))
    tmonth = qs_month["transaction_date__max"]
    if tmonth is None:
        tmonth = localtime(timezone.now())
    return tmonth


class BudgetListView(LoginRequiredMixin, TemplateView):
    """管理会計支出の予算・実績対比表
    - 予算実績対比表はログインユーザが閲覧可能とする。
    """

    model = ExpenseBudget
    template_name = "budget/budget_list.html"
    # permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(self.request.GET.get("year", localtime(timezone.now()).year))
        month = int(self.request.GET.get("month", 12))
        kind = int(self.request.GET.get("kind", 0))
        day = calendar.monthrange(year, month)[1]
        # 会計年度
        period = [0, 0]
        period[0] = timezone.datetime(year, 1, 1, 0, 0, 0)
        period[1] = timezone.datetime(year, month, day, 0, 0, 0)
        # 年間の支出予算
        qs_budget = (
            ExpenseBudget.objects.select_related("himoku")
            .filter(year=year)
            .filter(himoku__alive=True)
        )
        # 管理会計区分のみとしてfilterする。
        kanriclass_name = AccountingClass.get_class_name("管理")
        qs_budget = qs_budget.filter(
            himoku__accounting_class__accounting_name=kanriclass_name
        )
        # qs_budget = qs_budget.filter(himoku__alive=True)

        qs_budget = qs_budget.order_by("himoku__code")
        # 管理会計口座の累計支出
        if kind == 0:
            qs_expense = Transaction.objects.select_related("himoku")
        else:
            qs_expense = ReportTransaction.objects.select_related("himoku")
        # 入金以外（支出、資金移動）でfiler
        qs_expense = qs_expense.filter(himoku__is_income=False)
        # 計算対象でfilter
        qs_expense = qs_expense.filter(calc_flg=True)
        # 指定された「月度」までの期間でfilte
        qs_expense = qs_expense.filter(transaction_date__range=period).order_by(
            "himoku__code"
        )
        # 行の集約を行う前に最新月次データの月を取得する
        current_date = near_month(qs_expense)
        # 費目での集約を行う
        qs_expense = qs_expense.values(
            "himoku", "himoku__himoku_name", "himoku__accounting_class__accounting_name"
        ).annotate(ruiseki=Sum("ammount"))

        # 予算と累積支出
        compair_list = composit(qs_budget, qs_expense)
        # 表示される項目での合計を計算
        total_budget, total_ruiseki = get_total(compair_list)

        # 予算外支出を抽出する
        check_budget_list = check_budget(qs_budget, qs_expense)

        # forms.pyのKeikakuListFormに初期値を設定する
        form = Budget_listForm(
            initial={
                "year": year,
                "month": month,
                "kind": kind,
            }
        )
        context["form"] = form
        context["month"] = current_date.month
        context["expense_budget"] = compair_list
        context["total_budget"] = total_budget
        context["total_ruiseki"] = total_ruiseki
        context["check_budget"] = check_budget_list
        return context
