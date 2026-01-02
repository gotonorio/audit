import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from monthly_report.models import ReportTransaction
from passbook.forms import YearMonthForm
from passbook.utils import check_period, select_period
from record.models import Transaction

logger = logging.getLogger(__name__)


class IncosistencyCheckView(PermissionRequiredMixin, generic.TemplateView):
    """月次支出報告と通帳支払いデータの「不整合チェック」"""

    template_name = "check_record/expense_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # GETパラメータ(self.request.GET)
        now = localtime(timezone.now())
        year = self.request.GET.get("year") or now.year
        month = self.request.GET.get("month") or now.month

        year = int(year)
        month = int(month)

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
        # ---------------------------------------------------------------------
        # 月次報告データ
        # 入出金明細は町内会会計を含むため町内会費を除外しない。
        # ---------------------------------------------------------------------
        qs_mr = ReportTransaction.get_qs_mr(tstart, tend, 0, "expense", True).order_by(
            "is_netting", "himoku__himoku_name"
        )
        # 月次収支の支出合計（口座振替手数料を除く）
        total_mr = ReportTransaction.total_calc_flg(qs_mr.exclude(is_netting=True))
        # ---------------------------------------------------------------------
        # 入出金明細データ
        # ---------------------------------------------------------------------
        qs = (
            Transaction.objects.filter(transaction_date__range=[tstart, tend])
            .filter(is_income=False)
            .filter(himoku__aggregate_flag=True)
        )
        qs = qs.values("himoku__himoku_name").annotate(debt=Sum("amount")).order_by("himoku")
        # 入出金明細の「緑地維持管理費」を「全体利用施設管理料」に変更する。
        # qs_dict["全体利用施設管理料"] = qs_dict.pop["緑地維持管理費"]
        qs_list = list(qs)
        total_pb = 0
        for i in qs_list:
            total_pb += i["debt"]
            if i["himoku__himoku_name"] == "緑地維持管理費":
                i["himoku__himoku_name"] = "全体利用施設管理料"

        qs_list.sort(key=lambda x: x["himoku__himoku_name"])
        context["mr_list"] = qs_mr
        context["total_mr"] = total_mr
        context["pb_list"] = qs_list
        context["total_pb"] = total_pb
        context["form"] = form
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        context["year"] = year
        context["month"] = month

        return context
