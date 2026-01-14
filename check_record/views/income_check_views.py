import datetime
import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView
from monthly_report.models import BalanceSheet, ReportTransaction
from passbook.forms import YearMonthForm
from passbook.services import select_period
from record.models import Transaction

from check_record.mixins import IncomeCheckParamMixin
from check_record.services import calculate_netting_total, get_monthly_income_check_data

logger = logging.getLogger(__name__)


class MonthlyReportIncomeCheckView(PermissionRequiredMixin, IncomeCheckParamMixin, TemplateView):
    template_name = "check_record/kurasel_mr_income_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month = self.get_params()

        # Service層で一括集計
        data = get_monthly_income_check_data(year, month)

        # 計算ロジック（差額など）を整理
        total_mr_final = data["total_mr"] + data["total_mishuu_claim"]
        total_pb_final = data["total_pb"] + data["netting_total"]
        total_diff = (total_pb_final + data["total_last_maeuke"]) - total_mr_final

        context.update(
            {
                "year": data["year"],
                "month": data["month"],
                "yyyymm": f"{data['year']}年{data['month']}月",
                "mr_list": data["qs_mr"],
                "pb_list": data["qs_pb"],
                "netting_total": data["netting_total"],
                "mishuu_list": data["this_mishuu_bs"],
                "total_mishuu_bs": data["total_mishuu_bs"],
                "last_mishuu_bs": data["last_mishuu_bs"],
                "total_mishuu_claim": data["total_mishuu_claim"],
                "total_last_mishuu": data["total_last_mishuu"],
                "total_last_maeuke": data["total_last_maeuke"],
                "total_comment": data["total_comment"],
                "total_mr": total_mr_final,
                "total_pb": total_pb_final,
                "total_diff": total_diff,
                "check_last_mishuu": data["total_mishuu_claim"] - data["total_last_maeuke"],
                "form": YearMonthForm(initial={"year": data["year"], "month": data["month"]}),
                "this_maeuke_bs": data["this_maeuke_bs"],
                "total_maeuke_bs": data["total_maeuke_bs"],
            }
        )
        return context


class YearReportIncomeCheckView(PermissionRequiredMixin, IncomeCheckParamMixin, TemplateView):
    template_name = "check_record/year_income_check.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, _ = self.get_params()
        tstart, tend = select_period(year, 0)

        # 1. 月次報告年間合計 (Service化推奨だが、ここでは整理のみ)
        mr_year_income = ReportTransaction.get_year_income(tstart, tend, True).exclude(amount=0)
        total_year_income = sum(item["price"] for item in mr_year_income)

        # 2. 通帳年間合計
        start_date = datetime.date(2023, 4, 1)
        pb_year_income = (
            Transaction.get_year_income(tstart, tend, True)
            .filter(transaction_date__gte=start_date, himoku__aggregate_flag=True)
            .order_by("himoku")
        )
        total_pb_raw = sum(item["price"] for item in pb_year_income)

        # 3. 各種集計
        netting_total = calculate_netting_total(tstart, tend)

        # 前期・当期のBSデータ
        _, last_total_mishuu = BalanceSheet.get_mishuu_bs(*select_period(year - 1, 12))
        this_mishuu_bs, total_mishuu_bs = BalanceSheet.get_mishuu_bs(*select_period(year, 12))

        # 最終計算
        total_pb_final = total_pb_raw + netting_total - last_total_mishuu

        context.update(
            {
                "year": year,
                "year_list": mr_year_income,
                "pb_list": pb_year_income,
                "netting_total": netting_total,
                "pb_last_mishuukin": last_total_mishuu,
                "mishuu_list": this_mishuu_bs,
                "total_mishuu_bs": total_mishuu_bs,
                "total_mr": total_year_income,
                "total_pb": total_pb_final,
                "total_diff": total_pb_final - total_year_income,
                "form": YearMonthForm(initial={"year": year}),
            }
        )
        return context
