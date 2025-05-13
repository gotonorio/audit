import calendar
import logging

from budget.forms import Budget_listForm
from budget.models import ExpenseBudget
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.aggregates import Max, Sum
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.generic import TemplateView
from monthly_report.models import ReportTransaction
from record.models import AccountingClass, Transaction

logger = logging.getLogger(__name__)


def composit(budget, expense):
    """予算と累積支出をlistで返す
    - 年次予算の費目で集計する。
    - 実際に支出した項目（費目）が抜けるため使用しない。->見直す20241216
    - data[0]:費目名
    - data[1]:支出予算
    - data[2]:累積支出額
    - data[3]:残高（予算-支出額）、一度も支出がない費目の場合はdata[1]を設定する
    - data[4]:支出割合
    - data[5]:コメント
    """
    comp_list = []
    for d in budget:
        data = ["", 0, 0, 0, 0, ""]
        budget_himoku_id = d.himoku.id
        data[0] = d.himoku
        data[1] = d.budget_expense
        data[5] = d.comment
        for e in expense:
            if e["himoku"] == budget_himoku_id:
                data[2] = e["ruiseki"]
                data[3] = data[1] - data[2]
                if data[1] == 0:
                    data[4] = 0
                else:
                    data[4] = data[2] * 100 / data[1]
                break
            else:  # 一度も支出がない費目の場合
                data[3] = data[1]
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
        # 累積金額がある場合だけcomp_listに登録する
        if data[2] > 0:
            comp_list.append(data)
    return comp_list


def get_total(data_list):
    """表示されたデータでの合計を返す"""
    total_budget = 0
    total_ruikei = 0
    for data in data_list:
        total_budget += int(data[1])
        total_ruikei += int(data[2])
    return total_budget, total_ruikei


def near_month(qs):
    """月次報告の最新月を返す"""
    qs_month = qs.aggregate(Max("transaction_date"))
    tmonth = qs_month["transaction_date__max"]
    if tmonth is None:
        tmonth = localtime(timezone.now())
    return tmonth


class BudgetListView(LoginRequiredMixin, TemplateView):
    """会計支出の予算・実績対比表"""

    model = ExpenseBudget
    # 予算実績対比表はログインユーザが閲覧可能とするため下記をコメントアウト。
    # permission_required = ("record.view_transaction",)

    # templateファイルの切り替え
    def get_template_names(self):
        """templateファイルを切り替える"""
        if self.request.user_agent_flag == "mobile":
            template_name = "budget/budget_list_mobile.html"
        else:
            template_name = "budget/budget_list.html"
        return [template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(self.request.GET.get("year", localtime(timezone.now()).year))
        month = int(self.request.GET.get("month", localtime(timezone.now()).month))
        ac_class = self.request.GET.get("ac_class", 1)
        # 会計区分が指定されていなければ、管理会計を選択する。
        if ac_class == "":
            ac_class = 1
        # 月次報告データ(0)、入出金明細データ(1)の選択
        kind = int(self.request.GET.get("kind", 0))
        day = calendar.monthrange(year, month)[1]
        # 会計年度
        period = []
        period.append(timezone.datetime(year, 1, 1, 0, 0, 0))
        period.append(timezone.datetime(year, month, day, 0, 0, 0))
        # 年間の支出予算を抽出
        qs_budget = ExpenseBudget.get_expense_budget(year)
        # 会計区分名
        ac_class_name = AccountingClass.get_accountingclass_name(ac_class)
        # 会計予算の抽出
        (
            compair_list,
            current_date,
            total_budget,
            total_ruiseki,
            check_budget_list,
        ) = self.kanri_budget(qs_budget, ac_class_name, period, kind)

        # forms.pyのKeikakuListFormに初期値を設定する
        form = Budget_listForm(
            initial={
                "year": year,
                "month": month,
                "ac_class": ac_class,
                "kind": kind,
            }
        )
        context["title"] = ac_class_name
        context["form"] = form
        context["month"] = current_date.month
        context["expense_budget"] = compair_list
        context["total_budget"] = total_budget
        context["total_ruiseki"] = total_ruiseki
        context["check_budget"] = check_budget_list
        return context

    def kanri_budget(self, qs_budget, ac_class_name, period, kind):
        """管理会計予算"""
        # 指定された会計区分の予算を読み込む
        qs_budget = qs_budget.filter(himoku__accounting_class__accounting_name=ac_class_name)
        qs_budget = qs_budget.order_by("himoku__code")

        # 累計支出を算出する。デフォルトは月次報告のデータを使う。
        if kind == 0:
            qs_expense = ReportTransaction.objects.select_related("himoku")
        else:
            qs_expense = Transaction.objects.select_related("himoku")
        # 入金以外（支出、資金移動）でfiler
        qs_expense = qs_expense.filter(himoku__is_income=False)
        # 管理会計区分でfilter
        qs_expense = qs_expense.filter(himoku__accounting_class__accounting_name=ac_class_name)
        # 指定された「月度」までの期間でfilte
        qs_expense = qs_expense.filter(transaction_date__range=period).order_by("himoku__code")
        # 行の集約を行う前に最新月次データの月を取得する
        current_date = near_month(qs_expense)
        # 費目での集約を行う
        qs_expense = qs_expense.values(
            "himoku", "himoku__himoku_name", "himoku__accounting_class__accounting_name"
        ).annotate(ruiseki=Sum("amount"))

        # 予算と累積支出
        compair_list = composit(qs_budget, qs_expense)
        # 表示される項目での合計を計算
        total_budget, total_ruiseki = get_total(compair_list)

        # 予算外支出を抽出する
        check_budget_list = check_budget(qs_budget, qs_expense)

        return (
            compair_list,
            current_date,
            total_budget,
            total_ruiseki,
            check_budget_list,
        )
