import logging

from check_record.views.kurasel_views import get_lastmonth
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from kurasel_translator.my_lib.append_list import select_period
from kurasel_translator.my_lib.check_lib import check_period
from monthly_report.models import ReportTransaction
from passbook.forms import YearMonthForm
from record.models import Transaction

logger = logging.getLogger(__name__)


class IncosistencyCheckView(PermissionRequiredMixin, generic.TemplateView):
    """月次支出報告と通帳支払いデータの「不整合チェック」"""

    template_name = "check_record/expense_check.html"
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
        # 月次報告データ
        # ---------------------------------------------------------------------
        qs_mr = ReportTransaction.get_monthly_report_expense(tstart, tend).order_by("himoku__himoku_name")
        # 月次収支の支出合計（集計フラグがFalseの費目を除外する）
        qs_mr_without_netting = qs_mr.exclude(himoku__aggregate_flag=False)
        total_mr = ReportTransaction.calc_total_withflg(qs_mr_without_netting, True)
        # ---------------------------------------------------------------------
        # 入出金明細データ
        # 町内会会計を除外する（2024-11-14）
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
            logger.debug(i["debt"])
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
