import difflib
import logging
import re

from billing.models import Billing
from common.services import check_period, get_lastmonth, select_period
from django.conf import settings
from django.db.models import Sum
from monthly_report.models import BalanceSheet, ReportTransaction
from monthly_report.services.monthly_report_services import get_monthly_report_queryset
from payment.models import Payment
from record.models import ApprovalCheckData, ClaimData, Transaction

logger = logging.getLogger(__name__)


# -----------------------------------------
# 月次報告と通帳データの不整合チェック
# incosistency_check_views用service関数
# -----------------------------------------
def get_expense_inconsistency_summary(year, month):
    """月次報告と通帳データの不整合チェック用データを取得"""
    year, month = check_period(year, month)
    tstart, tend = select_period(year, month)

    # 1. 月次報告データ
    qs_mr = get_monthly_report_queryset(tstart, tend, 0, "expense", True).order_by(
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
# 請求金額内訳データと月次報告比較
# billing_check_views用service関数
# -----------------------------------------
def get_billing_check_service(year, month):
    """請求金額内訳データと月次報告比較用データを取得"""

    year, month = check_period(year, month)
    tstart, tend = select_period(year, month)

    # (1) 請求金額内訳データを抽出
    qs_billing = Billing.get_billing_data_qs(tstart, tend)
    # 表示順序
    qs_billing = qs_billing.order_by(
        "-billing_amount",
    )
    # 合計金額
    billing_total = Billing.calc_total_billing(qs_billing)

    # (2) 月次報告の収入データを抽出
    qs_mr = get_monthly_report_queryset(tstart, tend, 0, "income", True)
    # 収入のない費目は除く
    qs_mr = qs_mr.exclude(amount=0).order_by("-amount")
    # 月次収支の収入合計
    total_mr = ReportTransaction.total_calc_flg(qs_mr)

    # (3) 請求時点の未収金リストおよび未収金額
    total_mishuu_claim, _ = ClaimData.get_mishuu_claim(year, month)

    # (4) 月次収入報告と請求金額のチェック
    # 請求金額内訳データと月次報告データで金額が異なる費目名ペアを抽出する
    list_mr = []
    list_billing = []
    for i in qs_mr:
        list_mr.append([str(i.himoku), i.amount])
    for i in qs_billing:
        list_billing.append([str(i.billing_item), i.billing_amount])
    mismatch_data_list = get_himoku_name_fuzzy(list_mr, list_billing, cutoff=0.4)

    # (5) チェック結果を辞書で返す
    return {
        # 請求金額内訳データ
        "billing_list": qs_billing,
        "billing_total": billing_total,
        # 月次報告データ
        "mr_list": qs_mr,
        "total_mr": total_mr,
        # 請求時点の未収金
        "total_mishuu_claim": total_mishuu_claim,
        # 表示用パラメータ
        "yyyymm": str(year) + "年" + str(month) + "月",
        "year": year,
        "month": month,
        # 不整合データリスト
        "mismatch_data_list": mismatch_data_list if len(mismatch_data_list) > 0 else [],
    }


# -----------------------------------------
# 支払い承認データと入出金明細データの比較
# apploval_check_views用service関数
# -----------------------------------------
def get_apploval_check_service(year, month):
    """支払い承認データと入出金明細データの比較用データを取得"""

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
    # step1 摘要欄コメントで支払い承認の有無をチェックしてアップデートする。
    _ = update_transaction_approval_status(qs_pb)
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


def update_transaction_approval_status(transaction_queryset):
    """
    摘要欄のテキストを解析し、承認が必要かどうかを一括更新する
    """
    # 承認不要条件の取得
    check_criteria = ApprovalCheckData.objects.filter(alive=True)
    if not check_criteria:
        return

    # 正規表現パターンのリストを事前に作成（ループ内の処理を高速化）
    patterns = [re.compile(str(c.atext)) for c in check_criteria if c.atext]

    updated_objs = []

    for obj in transaction_queryset:
        description = str(obj.description or "")
        if not description:
            continue

        # いずれかのパターンにマッチするか確認
        is_match = any(p.search(description) for p in patterns)

        # 承認不要に該当し、かつ現在「承認必要」ならリストに追加
        if is_match and obj.is_approval:
            obj.is_approval = False
            updated_objs.append(obj)

    # まとめて更新
    if updated_objs:
        Transaction.objects.bulk_update(updated_objs, ["is_approval"])


def get_himoku_name_fuzzy(mr_list, billing_list, cutoff=0.4):
    """
    mr_list, billing_list: [[品名, 価格], ...] のリスト
    戻り値: [[月次収入費目名, 収入金額, 請求費目名, 請求金額], ...]
    """
    results = []

    # blling_listデータを検索しやすく整理 (文字列化を徹底)
    b_names = [str(item[0]) for item in billing_list]
    b_dict = {str(item[0]): item[1] for item in billing_list}

    # blling_listのうち、マッチング済み（処理済み）の名前を記録するセット
    matched_b_names = set()

    # 1. 月次収入報告の費目について、請求金額内訳データと照合
    for item_a in mr_list:
        name_a = str(item_a[0])
        price_a = item_a[1]

        # B店の中から似た名前を探す
        matches = difflib.get_close_matches(name_a, b_names, n=1, cutoff=cutoff)

        if matches:
            name_b = matches[0]
            price_b = b_dict[name_b]
            matched_b_names.add(name_b)  # 処理済みとして記録

            # 価格が異なる場合のみ追加
            if price_a != price_b:
                results.append([name_a, price_a, name_b, price_b])
        else:
            # B店に存在しない場合 (B価格を0にする)
            results.append([name_a, price_a, "（請求項目に該当なし）", 0])

    # 2. B店にしか存在しない（まだマッチングしていない）商品を抽出
    for name_b, price_b in b_dict.items():
        if name_b not in matched_b_names:
            # A店に存在しない場合 (A価格を0にする)
            results.append(["（月次報告に該当なし）", 0, name_b, price_b])

    return results
