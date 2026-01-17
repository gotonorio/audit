# check_record/services.py
import logging

from billing.models import Billing
from common.services import check_period, get_lastmonth, select_period
from django.conf import settings
from django.db.models import Sum
from monthly_report.models import BalanceSheet, ReportTransaction
from payment.models import Payment
from record.models import ClaimData, Transaction

logger = logging.getLogger(__name__)


# -----------------------------------------
# incosistency_check_views用service関数
# -----------------------------------------
def get_expense_inconsistency_summary(year, month):
    """月次報告と通帳データの不整合チェック用データを取得"""
    year, month = check_period(year, month)
    tstart, tend = select_period(year, month)

    # 1. 月次報告データ
    qs_mr = ReportTransaction.get_qs_mr(tstart, tend, 0, "expense", True).order_by(
        "is_netting", "himoku__himoku_name"
    )
    total_mr = ReportTransaction.total_calc_flg(qs_mr.exclude(is_netting=True))

    # 2. 通帳データ（集計）
    # values().annotate() でDB側で合計を算出
    qs_pb_agg = (
        Transaction.objects.filter(
            transaction_date__range=[tstart, tend], is_income=False, himoku__aggregate_flag=True
        )
        .values("himoku__himoku_name")
        .annotate(debt=Sum("amount"))
        .order_by("himoku")
    )

    # 3. ビジネスルール：費目名の読み替えと合計計算
    pb_list = list(qs_pb_agg)
    total_pb = 0
    for item in pb_list:
        total_pb += item["debt"]
        # 名称の読み替えロジック
        if item["himoku__himoku_name"] == "緑地維持管理費":
            item["himoku__himoku_name"] = "全体利用施設管理料"

    # 読み替え後に再ソート
    pb_list.sort(key=lambda x: x["himoku__himoku_name"])

    return {
        "year": year,
        "month": month,
        "mr_list": qs_mr,
        "total_mr": total_mr,
        "pb_list": pb_list,
        "total_pb": total_pb,
    }


# -----------------------------------------
# billing_check_views用service関数
# -----------------------------------------
def get_billing_check_service(year, month):
    """"""

    year, month = check_period(year, month)
    tstart, tend = select_period(year, month)

    # (1) 請求金額内訳データを抽出
    qs_billing = Billing.get_billing_list(tstart, tend)
    # 表示順序
    qs_billing = qs_billing.order_by(
        "-billing_amount",
    )
    # 合計金額
    billing_total = Billing.calc_total_billing(qs_billing)

    # (2) 月次収入データを抽出
    qs_mr = ReportTransaction.get_qs_mr(tstart, tend, 0, "income", True)
    # 収入のない費目は除く
    qs_mr = qs_mr.exclude(amount=0).order_by("-amount")
    # 月次収支の収入合計
    total_mr = ReportTransaction.total_calc_flg(qs_mr)

    # (3) 請求時点の未収金リストおよび未収金額
    total_mishuu_claim, _ = ClaimData.get_mishuu_claim(year, month)

    # (4) 月次収入報告と請求金額のチェック
    check_mismatch = []
    for i in qs_mr:
        chk = False
        for billing in qs_billing:
            if i.amount == billing.billing_amount:
                chk = True
                break
        if not chk:
            check_mismatch.append(i)

    return {
        # 請求金額内訳データ
        "billing_list": qs_billing,
        "billing_total": billing_total,
        "check_mismatch": check_mismatch,
        # 入出金明細データ
        "mr_list": qs_mr,
        "total_mr": total_mr,
        "total_mishuu_claim": total_mishuu_claim,
        "yyyymm": str(year) + "年" + str(month) + "月",
        "year": year,
        "month": month,
    }


# -----------------------------------------
# apploval_check_views用service関数
# -----------------------------------------
def get_apploval_check_service(year, month):
    """"""

    year, month = check_period(year, month)
    tstart, tend = select_period(year, month)

    # 前月の年月
    lastyear, lastmonth = get_lastmonth(year, month)

    # Kuraselによる会計処理は2023年4月以降。それ以前は表示しない。
    year, month = check_period(year, month)

    # 当月の抽出期間
    tstart, tend = select_period(year, month)
    # 前月の抽出期間
    last_tstart, last_tend = select_period(lastyear, lastmonth)

    # 支払い承認データ
    qs_payment, total_ap = Payment.kurasel_get_payment(tstart, tend)

    # 入出金明細データの取得
    qs_pb = Transaction.get_qs_pb(tstart, tend, "0", "0", "expense", True, False)
    qs_pb = qs_pb.order_by("transaction_date", "himoku__code")
    # step1 摘要欄コメントで支払い承認の有無をチェック。
    _ = Transaction.set_is_approval_text(qs_pb)
    # step2 費目で支払い承認の有無をチェック。
    _ = Transaction.set_is_approval_himoku(qs_pb)

    # 支出合計金額。（支払い承認が必要な費目だけの合計とする）
    total_pb = 0
    for d in qs_pb:
        if d.is_approval:
            total_pb += d.amount

    # 未払いデータ
    qs_this_miharai, total_miharai = BalanceSheet.get_miharai_bs(tstart, tend)

    # 前月の未払金
    qs_last_miharai = BalanceSheet.objects.filter(monthly_date__range=[last_tstart, last_tend]).filter(
        item_name__item_name__contains=settings.PAYABLE
    )
    # 前月の未収金合計
    total_last_miharai = 0
    for d in qs_last_miharai:
        total_last_miharai += d.amounts

    return {
        "mr_list": qs_payment,
        "pb_list": qs_pb,
        "total_mr": total_ap,
        "total_pb": total_pb,
        "total_diff": total_pb - total_ap,
        "yyyymm": str(year) + "年" + str(month) + "月",
        "this_miharai": qs_this_miharai,
        "this_miharai_total": total_miharai,
        "last_miharai_total": total_last_miharai,
        "year": year,
        "month": month,
    }
