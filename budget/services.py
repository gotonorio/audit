# budget/services.py
import calendar

from django.db.models import Max, Sum
from django.utils import timezone
from django.utils.timezone import localtime
from monthly_report.models import ReportTransaction
from record.models import AccountingClass, Transaction


def get_budget_vs_actual(year, month, ac_class_pk, kind):
    """
    予算と実績を比較したレポートデータを生成するメインサービス
    """
    # 1. 準備：期間と会計区分の取得
    last_day = calendar.monthrange(year, month)[1]
    start_date = timezone.datetime(year, 1, 1)
    end_date = timezone.datetime(year, month, last_day)

    ac_class = AccountingClass.objects.get(pk=ac_class_pk)

    # 2. 予算データの取得
    from .models import ExpenseBudget  # 循環インポート回避

    qs_budget = (
        ExpenseBudget.get_expense_budget(year)
        .filter(himoku__accounting_class=ac_class)
        .order_by("himoku__code")
    )

    # 3. 支出データの取得（実績）
    model = ReportTransaction if kind == 0 else Transaction
    qs_expense = model.objects.select_related("himoku").filter(
        himoku__is_income=False,
        himoku__accounting_class=ac_class,
        transaction_date__range=[start_date, end_date],
    )

    # 最新の月次データの日付を取得
    latest_date = qs_expense.aggregate(Max("transaction_date"))["transaction_date__max"] or localtime(
        timezone.now()
    )

    # 費目ごとに集約
    expense_data = qs_expense.values("himoku").annotate(ruiseki=Sum("amount"))
    expense_dict = {item["himoku"]: item["ruiseki"] for item in expense_data}

    # 4. データの照合 (Comparison)
    comparison_list = []
    total_budget = 0
    total_actual = 0

    for b in qs_budget:
        actual = expense_dict.get(b.himoku.id, 0)
        balance = b.budget_expense - actual
        ratio = (actual * 100 / b.budget_expense) if b.budget_expense > 0 else 0

        comparison_list.append(
            {
                "himoku": b.himoku,
                "budget": b.budget_expense,
                "actual": actual,
                "balance": balance,
                "ratio": ratio,
                "comment": b.comment,
            }
        )
        total_budget += b.budget_expense
        total_actual += actual

    # 5. 予算外支出のチェック
    budget_himoku_ids = [b.himoku.id for b in qs_budget]
    unbudgeted_list = []
    # 予算に含まれていないが支出があるものを抽出
    for item in expense_data:
        if item["himoku"] not in budget_himoku_ids and item["ruiseki"] > 0:
            # 詳細情報の取得（最適化のため、必要に応じて検討）
            from record.models import Himoku

            himoku = Himoku.objects.select_related("accounting_class").get(pk=item["himoku"])
            unbudgeted_list.append(
                {
                    "ac_name": himoku.accounting_class.accounting_name,
                    "himoku_name": himoku.himoku_name,
                    "actual": item["ruiseki"],
                }
            )

    return {
        "comparison_list": comparison_list,
        "total_budget": total_budget,
        "total_actual": total_actual,
        "unbudgeted_list": unbudgeted_list,
        "latest_month": latest_date.month,
        "ac_class_name": ac_class.accounting_name,
    }
