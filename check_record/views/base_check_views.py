import datetime
import logging

from billing.models import Billing
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from monthly_report.models import BalanceSheet, ReportTransaction
from passbook.forms import YearMonthForm
from passbook.utils import check_period, get_lastmonth, select_period
from payment.models import Payment
from record.models import ClaimData, Transaction

logger = logging.getLogger(__name__)


class ApprovalExpenseCheckView(PermissionRequiredMixin, generic.TemplateView):
    """支払い承認データと入出金明細データの月別比較リスト
    - 入出金データの合計では、承認不要費目（資金移動、共用部電気料等）を除外する。
    - 未払金（貸借対照表データ）の表示。
    """

    template_name = "check_record/kurasel_ap_expense_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            year = kwargs.get("year")
            month = kwargs.get("month")
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)

        # 前月の年月
        lastyear, lastmonth = get_lastmonth(year, month)

        # Kuraselによる会計処理は2023年4月以降。それ以前は表示しない。
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
        # 支払い承認データ
        # ---------------------------------------------------------------------
        qs_payment, total_ap = Payment.kurasel_get_payment(tstart, tend)

        # ---------------------------------------------------------------------
        # 入出金明細データの取得
        # ---------------------------------------------------------------------
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

        # ---------------------------------------------------------------------
        # 未払いデータ
        # ---------------------------------------------------------------------
        qs_this_miharai, total_miharai = BalanceSheet.get_miharai_bs(tstart, tend)

        # 前月の未払金
        qs_last_miharai = BalanceSheet.objects.filter(monthly_date__range=[last_tstart, last_tend]).filter(
            item_name__item_name__contains=settings.PAYABLE
        )
        # 前月の未収金合計
        total_last_miharai = 0
        for d in qs_last_miharai:
            total_last_miharai += d.amounts

        context["mr_list"] = qs_payment
        context["pb_list"] = qs_pb
        context["total_mr"] = total_ap
        context["total_pb"] = total_pb
        context["total_diff"] = total_pb - total_ap
        context["form"] = form
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["this_miharai"] = qs_this_miharai
        context["this_miharai_total"] = total_miharai
        context["last_miharai_total"] = total_last_miharai
        context["year"] = year
        context["month"] = month

        return context


class BillingAmountCheckView(PermissionRequiredMixin, generic.TemplateView):
    """請求金額内訳データと口座収入データの月別比較リスト"""

    template_name = "check_record/kurasel_ba_income_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            year = kwargs.get("year")
            month = kwargs.get("month")
        else:
            year = self.request.GET.get("year", localtime(timezone.now()).year)
            month = self.request.GET.get("month", localtime(timezone.now()).month)

        # 当月の抽出期間
        tstart, tend = select_period(year, month)
        # forms.pyのKeikakuListFormに初期値を設定する
        form = YearMonthForm(
            initial={
                "year": year,
                "month": month,
            }
        )

        # ---------------------------------------------------------------------
        # (1) 請求金額内訳データを抽出
        # ---------------------------------------------------------------------
        qs_ba = Billing.get_billing_list(tstart, tend)
        # 表示順序
        qs_ba = qs_ba.order_by(
            "billing_item__code",
        )
        # 合計金額
        billing_total = Billing.calc_total_billing(qs_ba)

        # ---------------------------------------------------------------------
        # (2) 入出金明細データ（通帳データ）の収入リスト
        # ---------------------------------------------------------------------
        qs_pb = Transaction.get_qs_pb(tstart, tend, "0", "0", "income", True, False)
        # 2023年3月以前のデータを除外する。
        start_date = datetime.date(2023, 4, 1)
        qs_pb = qs_pb.filter(transaction_date__gte=start_date)
        # 資金移動は除く
        qs_pb = qs_pb.filter(himoku__aggregate_flag=True).order_by("transaction_date", "himoku")
        # 収入合計金額（資金移動でなく、前受金でない収入合計）
        total_pb, _ = Transaction.total_without_calc_flg(qs_pb.filter(is_billing=True))

        # ---------------------------------------------------------------------
        # (3) 自動控除された口座振替手数料。
        # ---------------------------------------------------------------------
        qs_is_netting = ReportTransaction.objects.filter(transaction_date__range=[tstart, tend])
        qs_is_netting = qs_is_netting.filter(is_netting=True)
        dict_is_netting = qs_is_netting.aggregate(netting_total=Sum("amount"))
        netting_total = dict_is_netting["netting_total"]
        # 相殺項目合計が存在しない場合をチェック
        if netting_total is None:
            netting_total = 0

        # ---------------------------------------------------------------------
        # (4) 当月の口座振替不備分を求める
        # ---------------------------------------------------------------------
        _, transfer_error = ClaimData.get_claim_list(tstart, tend, "振替不備")
        # if settings.DEBUG:
        #     logger.debug(transfer_error)

        # 請求金額内訳データ
        context["billing_list"] = qs_ba
        context["billing_total"] = billing_total
        # 入出金明細データ
        context["pb_list"] = qs_pb
        # ネッティング額（相殺処理額）
        context["netting_total"] = netting_total
        # 入出金明細データの合計（前受金は月次報告で処理のため合計には加えない）
        context["total_pb"] = total_pb + netting_total
        context["form"] = form
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["year"] = year
        context["month"] = month
        # 請求金額と収入金額の差
        context["total_diff"] = total_pb + netting_total - billing_total
        # 当月の口座振替不備
        context["transfer_error"] = transfer_error
        return context
