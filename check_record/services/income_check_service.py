import datetime
import logging

from billing.models import Billing
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from monthly_report.models import BalanceSheet, ReportTransaction
from passbook.services import check_period, get_lastmonth, select_period
from payment.models import Payment
from record.models import ClaimData, Transaction

logger = logging.getLogger(__name__)


def calculate_netting_total(tstart, tend):
    """相殺項目（手数料など）の合計を計算"""
    result = ReportTransaction.objects.filter(
        transaction_date__range=[tstart, tend], is_netting=True
    ).aggregate(total=Coalesce(Sum("amount"), 0))
    return result["total"]


# -----------------------------------------
# income_check_views.py用service関数
# -----------------------------------------
def get_monthly_income_check_data(year, month):
    """月次収入チェックに必要なデータを集計する"""
    year, month = check_period(year, month)
    last_year, last_month = get_lastmonth(year, month)

    tstart, tend = select_period(year, month)
    last_tstart, last_tend = select_period(last_year, last_month)

    # 1. 月次報告データ (MR)
    qs_mr = ReportTransaction.get_qs_mr(tstart, tend, 0, "income", True).exclude(amount=0).order_by("himoku")
    total_mr = ReportTransaction.total_calc_flg(qs_mr)

    # 2. 通帳データ (PB)
    start_limit = datetime.date(2023, 4, 1)
    qs_pb = (
        Transaction.get_qs_pb(tstart, tend, "0", "0", "income", True, False)
        .filter(transaction_date__gte=start_limit, himoku__aggregate_flag=True)
        .order_by("transaction_date", "himoku")
    )
    total_pb, _ = Transaction.total_without_calc_flg(qs_pb)

    # 3. 貸借対照表から「前受金」を読み込む
    this_maeuke_bs, total_maeuke_bs = BalanceSheet.get_maeuke_bs(tstart, tend)

    total_last_maeuke_claim, _, total_comment = ClaimData.get_maeuke_claim(year, month)
    # 4. 請求データから「未収金」を読み込む
    total_mishuu_claim, _ = ClaimData.get_mishuu_claim(year, month)

    # 5. 貸借対象表から当月の「未収金」を読み込む
    this_mishuu_bs, total_mishuu_bs = BalanceSheet.get_mishuu_bs(tstart, tend)
    last_mishuu_bs, total_last_mishuu_bs = BalanceSheet.get_mishuu_bs(last_tstart, last_tend)

    # 6. 特殊ルール（開始月判定）
    if year == settings.START_KURASEL["year"] and month == settings.START_KURASEL["month"]:
        total_last_mishuu_bs = settings.MISHUU_KANRI + settings.MISHUU_SHUUZEN + settings.MISHUU_PARKING

    # 7. 相殺額
    netting_total = calculate_netting_total(tstart, tend)

    return {
        "qs_mr": qs_mr,
        "total_mr": total_mr,
        "qs_pb": qs_pb,
        "total_pb": total_pb,
        "total_last_maeuke_claim": total_last_maeuke_claim,
        "total_comment": total_comment,
        "total_mishuu_claim": total_mishuu_claim,
        "this_mishuu_bs": this_mishuu_bs,
        "total_mishuu_bs": total_mishuu_bs,
        "last_mishuu_bs": last_mishuu_bs,
        "total_last_mishuu_bs": total_last_mishuu_bs,
        "netting_total": netting_total,
        "year": year,
        "month": month,
        "this_maeuke_bs": this_maeuke_bs,
        "total_maeuke_bs": total_maeuke_bs,
    }
