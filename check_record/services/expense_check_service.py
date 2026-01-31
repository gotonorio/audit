import logging

from common.services import check_period, get_lastmonth, select_period
from django.conf import settings
from django.utils import timezone
from monthly_report.models import BalanceSheet, ReportTransaction
from monthly_report.services.monthly_report_services import get_monthly_report_queryset
from record.models import Transaction

logger = logging.getLogger(__name__)


# -----------------------------------------
# expense_check_views.py用service関数
# -----------------------------------------
def get_monthly_expense_check_data(year, month):
    """月次支出チェックに必要なデータを集計する"""
    year, month = check_period(year, month)
    last_year, last_month = get_lastmonth(year, month)

    tstart, tend = select_period(year, month)
    last_tstart, last_tend = select_period(last_year, last_month)

    # 1. 月次報告データ
    qs_mr = get_monthly_report_queryset(tstart, tend, 0, "expense", True).exclude(is_netting=True)
    # 合計計算（集計対象外フラグを除外して計算）
    total_mr = ReportTransaction.total_calc_flg(qs_mr.exclude(himoku__aggregate_flag=False))

    # 2. 通帳データ
    qs_pb = Transaction.get_qs_pb(tstart, tend, "0", "0", "expense", True, False).order_by(
        "himoku__code", "transaction_date"
    )
    # 通帳合計の計算 (特定の費目条件を考慮)
    total_pb = sum(
        d.amount for d in qs_pb if d.himoku and d.himoku.aggregate_flag and not d.himoku.is_community
    )

    # 3. 未払金データ
    qs_this_miharai, total_this_miharai = BalanceSheet.get_miharai_bs(tstart, tend)
    _, total_last_miharai = BalanceSheet.get_miharai_bs(last_tstart, last_tend)

    # Kurasel開始月の特殊処理
    if int(year) == settings.START_KURASEL["year"] and int(month) == settings.START_KURASEL["month"]:
        total_last_miharai = settings.MIHARAI_INITIAL

    return {
        "qs_mr": qs_mr,
        "total_mr": total_mr,
        "qs_pb": qs_pb,
        "total_pb": total_pb,
        "qs_this_miharai": qs_this_miharai,
        "total_this_miharai": total_this_miharai,
        "total_last_miharai": total_last_miharai,
        "year": year,
        "month": month,
    }


def get_yearly_expense_check_data(year):
    """年間支出チェックに必要なデータを集計する"""
    tstart, tend = select_period(year, 0)

    # 1. 月次報告年間支出
    mr_year_expense = ReportTransaction.get_year_expense(tstart, tend).exclude(amount=0)
    total_mr_expense = sum(
        i["price"] for i in mr_year_expense if i["himoku__aggregate_flag"] and i["calc_flg"]
    )

    # 2. 通帳年間支出
    pb_year_expense = Transaction.get_year_expense(tstart, tend).order_by("himoku")
    total_pb_expense = sum(i["price"] for i in pb_year_expense)

    # 3. 当年12月の未払金
    tstart_12 = timezone.datetime(int(year), 12, 1, 0, 0, 0)
    tend_12 = timezone.datetime(int(year), 12, 31, 23, 59, 59)
    qs_this_miharai, total_this_miharai = BalanceSheet.get_miharai_bs(tstart_12, tend_12)

    return {
        "year_list": mr_year_expense,
        "total_mr": total_mr_expense,
        "pb_list": pb_year_expense,
        "total_pb": total_pb_expense,
        "this_miharai_list": qs_this_miharai,
        "total_this_miharai": total_this_miharai,
    }
