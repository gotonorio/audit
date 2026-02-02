import calendar

from django.conf import settings
from django.db.models import Case, IntegerField, Sum, When
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.timezone import localtime
from monthly_report.models import AccountingClass, ReportTransaction


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
        # 月初と月末の日付を設定
        month_period[0] = timezone.datetime(year, month, 1, 0, 0, 0)
        month_period[1] = timezone.datetime(year, month, day, 0, 0, 0)
        period.append(month_period)
    return period


def get_allmonths_data(qs, year):
    """年間の月毎、費目毎金額の集計（リファクタリング版）"""
    # 日付の期間を作成
    period = get_year_period(int(year))

    # 1. 12ヶ月分の集計条件を辞書内包処理で作る
    # month1=Sum(Case(When(transaction_date__range=[period[0][0], period[0][1]], then="amount",), default=0,)),
    # month2=Sum(Case(When(transaction_date__range=[period[1][0], period[1][1]], then="amount",), default=0,)),
    monthly_queries = {
        f"month{i + 1}": Sum(
            Case(
                When(transaction_date__range=[p[0], p[1]], then="amount"),
                default=0,
                output_field=IntegerField(),
            )
        )
        for i, p in enumerate(period)
    }

    # 2. 全期間の合計（total）を追加
    monthly_queries["total"] = Sum(
        Case(
            When(transaction_date__range=[period[0][0], period[11][1]], then="amount"),
            default=0,
            output_field=IntegerField(),
        )
    )

    # 3. 辞書を展開（**）して annotate に渡す
    return (
        qs.values("himoku__himoku_name", "himoku__accounting_class__accounting_name")
        .annotate(**monthly_queries)
        .order_by("himoku__accounting_class__code", "himoku__code")
    )


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
    qs = get_monthly_report_queryset(tstart, tend, ac_class, "income", True)
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


def get_monthly_report_queryset(tstart, tend, ac_class, inout_flg, community):
    """
    指定された条件に基づいて月次収支レポートのQuerySetを取得する
    """
    # 基本となるQuerySet (select_relatedでパフォーマンス最適化)
    qs = ReportTransaction.objects.select_related("himoku", "accounting_class")

    # (1) 期間と有効データでフィルタリング
    qs = qs.filter(transaction_date__range=[tstart, tend], delete_flg=False, himoku__alive=True).exclude(
        amount=0
    )

    # (2) 収入・支出の切り替え
    if inout_flg == "income":
        qs = qs.filter(himoku__is_income=True)
    elif inout_flg == "expense":
        qs = qs.filter(himoku__is_income=False)

    # (3) 特定の会計区分でフィルタリング (0より大きい場合)
    if ac_class > 0:
        qs = qs.filter(himoku__accounting_class=ac_class)

    # (4) 町内会会計の除外処理
    if not community:
        # 名称からオブジェクトを特定するロジックをここに集約
        town_class_name = AccountingClass.get_class_name("町内会")
        town_obj = AccountingClass.get_accountingclass_obj(town_class_name)
        if town_obj:
            qs = qs.exclude(himoku__accounting_class=town_obj.pk)

    return qs.order_by("accounting_class", "himoku__code")
