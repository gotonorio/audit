import logging

from billing.models import Billing
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from monthly_report.models import ReportTransaction
from passbook.forms import YearMonthForm
from passbook.utils import select_period
from record.models import ClaimData

logger = logging.getLogger(__name__)


class BillingAmountCheckView(PermissionRequiredMixin, generic.TemplateView):
    """請求金額内訳データと月次報告比較リスト"""

    template_name = "check_record/billing_income_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # GETパラメータ(self.request.GET)
        now = localtime(timezone.now())
        year = self.request.GET.get("year") or now.year
        month = self.request.GET.get("month") or now.month

        year = int(year)
        month = int(month)

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
        qs_billing = Billing.get_billing_list(tstart, tend)
        # 表示順序
        qs_billing = qs_billing.order_by(
            "-billing_amount",
        )
        # 合計金額
        billing_total = Billing.calc_total_billing(qs_billing)

        # ---------------------------------------------------------------------
        # (2) 月次収入データを抽出
        # ---------------------------------------------------------------------
        qs_mr = ReportTransaction.get_qs_mr(tstart, tend, 0, "income", True)
        # 収入のない費目は除く
        qs_mr = qs_mr.exclude(amount=0).order_by("-amount")
        # 月次収支の収入合計
        total_mr = ReportTransaction.total_calc_flg(qs_mr)

        # ---------------------------------------------------------------------
        # (3) 請求時点の未収金リストおよび未収金額
        # ---------------------------------------------------------------------
        total_mishuu_claim, _ = ClaimData.get_mishuu(year, month)

        # ---------------------------------------------------------------------
        # (4) 月次収入報告と請求金額のチェック
        # ---------------------------------------------------------------------
        check_mismatch = []
        for i in qs_mr:
            chk = False
            for billing in qs_billing:
                if i.amount == billing.billing_amount:
                    chk = True
                    break
            if not chk:
                check_mismatch.append(i)

        # 請求金額内訳データ
        context["billing_list"] = qs_billing
        context["billing_total"] = billing_total
        context["check_mismatch"] = check_mismatch
        # 入出金明細データ
        context["mr_list"] = qs_mr
        context["total_mr"] = total_mr
        context["total_mishuu_claim"] = total_mishuu_claim
        context["form"] = form
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["year"] = year
        context["month"] = month
        return context
