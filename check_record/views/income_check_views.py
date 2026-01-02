import datetime
import logging

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from monthly_report.models import BalanceSheet, ReportTransaction
from passbook.forms import YearMonthForm
from passbook.utils import check_period, get_lastmonth, select_period
from record.models import ClaimData, Transaction

logger = logging.getLogger(__name__)


class MonthlyReportIncomeCheckView(PermissionRequiredMixin, generic.TemplateView):
    """月次報告の収入データと口座収入データの月別比較リスト"""

    template_name = "check_record/kurasel_mr_income_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # GETパラメータ(self.request.GET)
        now = localtime(timezone.now())
        year = self.request.GET.get("year") or now.year
        month = self.request.GET.get("month") or now.month

        year = int(year)
        month = int(month)

        # 前月の年月
        lastyear, lastmonth = get_lastmonth(year, month)

        # 追加contextデータの初期化
        context["netting_total"] = 0
        context["total_last_maeuke"] = 0
        context["total_mishuu_bs"] = 0
        context["total_mishuu_claim"] = 0
        context["total_last_mishuu"] = 0
        context["total_mr"] = 0
        context["total_pb"] = 0

        # Kuraselによる会計処理は2023年4月以降。
        year, month = check_period(year, month)

        # formの初期値を設定する。
        form = YearMonthForm(
            initial={
                "year": year,
                "month": month,
            }
        )

        # 当月の抽出期間
        tstart, tend = select_period(year, month)
        # 前月の抽出期間
        last_tstart, last_tend = select_period(lastyear, lastmonth)

        # ---------------------------------------------------------------------
        # (1) 月次収入データを抽出
        # ---------------------------------------------------------------------
        qs_mr = ReportTransaction.get_qs_mr(tstart, tend, 0, "income", True)
        # 収入のない費目は除く
        qs_mr = qs_mr.exclude(amount=0).order_by("himoku")
        # 月次収支の収入合計(町内会会計含む)
        total_mr = ReportTransaction.total_calc_flg(qs_mr)

        # ---------------------------------------------------------------------
        # (2) 入出金明細データ（通帳データ）の収入リスト
        # ---------------------------------------------------------------------
        qs_pb = Transaction.get_qs_pb(tstart, tend, "0", "0", "income", True, False)
        # Kuraselデータは2は23年3月以降
        start_date = datetime.date(2023, 4, 1)
        qs_pb = qs_pb.filter(transaction_date__gte=start_date)
        # 資金移動は除く
        qs_pb = qs_pb.filter(himoku__aggregate_flag=True).order_by("transaction_date", "himoku")
        # 収入合計金額（資金移動でなく、前受金でない収入合計）
        total_pb, _ = Transaction.total_without_calc_flg(qs_pb)

        # ---------------------------------------------------------------------
        # (3) 請求時点前受金リスト（当月使用する前受金）
        # ---------------------------------------------------------------------
        total_last_maeuke, qs_last_maeuke, total_comment = ClaimData.get_maeuke_claim(year, month)

        # ---------------------------------------------------------------------
        # (3-1) 前月の貸借対照表データから当月の前受金を取得する。
        #       請求時前受金と貸借対照表の前月前受金を比較する。
        # ---------------------------------------------------------------------
        total_last_maeuke_bs = BalanceSheet.get_maeuke_bs(last_tstart, last_tend)

        # ---------------------------------------------------------------------
        # (4) 請求時点の未収金リストおよび未収金額
        # ---------------------------------------------------------------------
        total_mishuu_claim, qs_mishuu = ClaimData.get_mishuu(year, month)
        # 確認のため貸借対照表データから前月の未収金を計算する。
        last_mishuu_bs, total_last_mishuu = BalanceSheet.get_mishuu_bs(last_tstart, last_tend)
        check_last_mishuu = total_mishuu_claim - total_last_maeuke

        # ---------------------------------------------------------------------
        # (5) 貸借対照表データから当月の未収金を取得する。
        # ---------------------------------------------------------------------
        qs_mishuu_bs, total_mishuu_bs = BalanceSheet.get_mishuu_bs(tstart, tend)

        # ---------------------------------------------------------------------
        # (6) 自動控除費目（相殺費目）の金額を求める。（口座振替手数料）
        #     aggregateで集約する場合は抽出結果がDictとなる
        # ---------------------------------------------------------------------
        qs_is_netting = ReportTransaction.objects.filter(transaction_date__range=[tstart, tend])
        qs_is_netting = qs_is_netting.filter(is_netting=True)
        qs_is_netting = qs_is_netting.aggregate(netting_total=Sum("amount"))
        netting_total = qs_is_netting["netting_total"]
        # 相殺項目合計が存在しない場合をチェック
        if netting_total is None:
            netting_total = 0
        # 2023年4月度の処理。Kurasel監査の開始月（2023年4月）前月の未収金は規定値とする。
        if year == settings.START_KURASEL["year"] and month == settings.START_KURASEL["month"]:
            total_last_mishuu = settings.MISHUU_KANRI + settings.MISHUU_SHUUZEN + settings.MISHUU_PARKING

        # 月次収入データ
        context["mr_list"] = qs_mr
        # 入出金明細データ
        context["pb_list"] = qs_pb
        # ネッティング額（相殺処理額）
        context["netting_total"] = netting_total
        # 貸借対照表上の未収金リストと未収金額
        context["mishuu_list"] = qs_mishuu_bs
        context["total_mishuu_bs"] = total_mishuu_bs
        # 貸借対照表上の前月未収金額
        context["last_mishuu_bs"] = last_mishuu_bs
        # 請求時点未収金一覧の合計
        context["total_mishuu_claim"] = total_mishuu_claim
        # 前月の貸借対照表データの未収金
        context["total_last_mishuu"] = total_last_mishuu
        # 使用する前受金の合計
        # context["total_last_maeuke"] = total_last_maeuke
        context["total_last_maeuke"] = total_last_maeuke
        context["total_comment"] = total_comment
        # 月次収入データの合計
        context["total_mr"] = total_mr + total_mishuu_claim
        # 入出金明細データの合計
        context["total_pb"] = total_pb + netting_total
        # 収入差額＝（通帳収入＋口座振替手数料＋前受金）-（月次報告収入＋前月の未収金）
        context["total_diff"] = (context["total_pb"] + total_last_maeuke) - (total_mr + total_mishuu_claim)
        # formデータ
        context["form"] = form
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["year"] = year
        context["month"] = month
        # 「前受金を考慮した月次報告の未収金額」と「前月の貸借対照表での未収金額」をチェックする
        context["check_last_mishuu"] = check_last_mishuu
        return context


class YearReportIncomeCheckView(PermissionRequiredMixin, generic.TemplateView):
    """月次報告の年間収入データと口座収入データの比較リスト"""

    template_name = "check_record/year_income_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            year = kwargs.get("year")
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)

        # formの初期値を設定する。
        form = YearMonthForm(
            initial={
                "year": year,
            }
        )

        # 当月の抽出期間
        tstart, tend = select_period(year, 0)

        # ---------------------------------------------------------------------
        # (1) 月次報告の年間収入リスト
        # ---------------------------------------------------------------------
        mr_year_income = ReportTransaction.get_year_income(tstart, tend, True)
        # 収入のない費目は除く
        mr_year_income = mr_year_income.exclude(amount=0)
        # 年間収入の合計
        total_year_income = 0
        for i in mr_year_income:
            total_year_income += i["price"]

        # ---------------------------------------------------------------------
        # (2) 入出金明細データ（通帳データ）の年間収入リスト
        # ---------------------------------------------------------------------
        pb_year_income = Transaction.get_year_income(tstart, tend, True)
        # 2023年3月以前のデータを除外する。
        start_date = datetime.date(2023, 4, 1)
        pb_year_income = pb_year_income.filter(transaction_date__gte=start_date)
        # 資金移動は除く
        pb_year_income = pb_year_income.filter(himoku__aggregate_flag=True).order_by("himoku")
        # 収入合計金額
        total_pb = 0
        for i in pb_year_income:
            total_pb += i["price"]

        # ---------------------------------------------------------------------
        # (3) 貸借対照表データから当年12月の未収金を計算する。
        # ---------------------------------------------------------------------
        start_date, end_date = select_period(year, 12)
        qs_mishuu_bs, total_mishuu_bs = BalanceSheet.get_mishuu_bs(start_date, end_date)

        # ---------------------------------------------------------------------
        # (4) 自動控除された口座振替手数料。 自動控除費目の当月分金額を求める。
        # ---------------------------------------------------------------------
        qs_is_netting = ReportTransaction.objects.filter(transaction_date__range=[tstart, tend])
        qs_is_netting = qs_is_netting.filter(is_netting=True)
        dict_is_netting = qs_is_netting.aggregate(netting_total=Sum("amount"))
        netting_total = dict_is_netting["netting_total"]
        # 相殺項目合計が存在しない場合をチェック
        if netting_total is None:
            netting_total = 0

        # ---------------------------------------------------------------------
        # (5) 貸借対照表データから前期の未収金額を求める。
        # ---------------------------------------------------------------------
        last_start_date, last_end_date = select_period(int(year) - 1, 12)
        _, last_total_mishuu = BalanceSheet.get_mishuu_bs(last_start_date, last_end_date)

        # 月次収入データ
        context["year_list"] = mr_year_income
        # 入出金明細データ
        context["pb_list"] = pb_year_income
        # ネッティング額（相殺処理額）
        context["netting_total"] = netting_total
        # 前期の未収金
        context["pb_last_mishuukin"] = last_total_mishuu
        # 貸借対照表上の未収金リストと未収金額
        context["mishuu_list"] = qs_mishuu_bs
        context["total_mishuu_bs"] = total_mishuu_bs
        # 月次収入データの合計
        context["total_mr"] = total_year_income
        # 入出金明細データの合計
        context["total_pb"] = total_pb + netting_total - last_total_mishuu
        context["total_diff"] = context["total_pb"] - total_year_income
        context["form"] = form
        context["year"] = year
        return context
