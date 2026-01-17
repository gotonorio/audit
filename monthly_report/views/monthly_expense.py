import logging

from common.services import select_period
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.generic import DeleteView, UpdateView
from record.models import AccountingClass

from monthly_report.forms import MonthlyReportExpenseForm
from monthly_report.models import ReportTransaction

from .base import MonthlyReportBaseView

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# ListView
# ----------------------------------------------------------------------------
class MonthlyReportExpenseListView(MonthlyReportBaseView):
    template_name = "monthly_report/monthly_report_expense.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month, ac_class = self.get_year_month_ac(kwargs)

        tstart, tend = select_period(year, month)

        ac_obj = AccountingClass.get_accountingclass_obj(AccountingClass.get_class_name("町内会"))

        is_chonaikai = ac_obj.pk == int(ac_class)
        qs = ReportTransaction.get_qs_mr(tstart, tend, ac_class, "expense", is_chonaikai)

        context["transaction_list"] = qs.order_by(
            "himoku__accounting_class",
            "himoku__code",
            "calc_flg",
            "transaction_date",
        )
        context["total_withdrawals"] = ReportTransaction.total_calc_flg(qs)
        context["yyyymm"] = f"第{year - settings.FIRST_PERIOD_YEAR}期{month}月"

        return self.base_context(context, year, month, ac_class)


# ----------------------------------------------------------------------------
# UpdateView
# ----------------------------------------------------------------------------
class MonthlyReportExpenseUpdateView(PermissionRequiredMixin, UpdateView):
    """月次報告 支出データアップデートView"""

    model = ReportTransaction
    form_class = MonthlyReportExpenseForm
    template_name = "monthly_report/monthly_report_form.html"
    permission_required = "record.add_transaction"

    # 保存が成功した場合に遷移するurl
    def get_success_url(self):
        """保存成功後、GETパラメータを付与した一覧画面へリダイレクト"""
        base_url = reverse("monthly_report:expenselist")

        # クエリパラメータを辞書形式で定義
        params = urlencode(
            {
                "year": self.object.transaction_date.year,
                "month": self.object.transaction_date.month,
                "accounting_class": self.object.himoku.accounting_class.id,
            }
        )
        return f"{base_url}?{params}"

    def form_valid(self, form):
        # commitを停止する。
        self.object = form.save(commit=False)
        # # transaction_dateを YYYY-MM-01に強制的に修正する。
        # self.object.transaction_date = self.object.transaction_date.replace(day=1)
        # updated_dateをセット。
        self.object.author = self.request.user
        self.object.created_date = timezone.now()
        # ログの記録
        msg = (
            f"{self.object.created_date.date()}"
            f"費目名「{self.object.himoku}」"
            f"金額「{self.object.amount:,}」"
            f"修正者「{self.request.user}」"
        )
        logger.info(msg)
        # データを保存。
        self.object.save()
        return super().form_valid(form)


# ----------------------------------------------------------------------------
# DeleteView
# ----------------------------------------------------------------------------
class DeleteExpenseView(PermissionRequiredMixin, DeleteView):
    """月次報告支出データ削除View"""

    model = ReportTransaction
    template_name = "monthly_report/reporttransaction_confirm_delete.html"
    permission_required = "record.add_transaction"

    def get_success_url(self):
        base_url = reverse("monthly_report:expenselist")

        # クエリパラメータを辞書形式で定義
        params = urlencode(
            {
                "year": self.object.transaction_date.year,
                "month": self.object.transaction_date.month,
                "accounting_class": self.object.himoku.accounting_class.id,
            }
        )
        return f"{base_url}?{params}"

    def form_valid(self, form):
        """djang 4.0で、delete()で行う処理はform_valid()を使うようになったみたい。
        https://stackoverflow.com/questions/53145279/edit-record-before-delete-django-deleteview
        """
        # ログに削除の情報を記録する
        logger.info(
            f"費目「{self.object.himoku}」"
            f"金額「{self.object.amount:,}」"
            f"摘要「{self.object.description}」"
            f"削除者「{self.request.user}」"
        )
        # メッセージ表示
        messages.success(self.request, "削除しました。")
        return super().form_valid(form)
