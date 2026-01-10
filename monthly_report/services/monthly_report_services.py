import calendar

from django.conf import settings
from django.db.models import Case, Sum, When
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.timezone import localtime
from monthly_report.models import ReportTransaction


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
    """月次報告の年間収入データを返す"""
    # 月次報告収入リスト
    qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "income", True)
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
