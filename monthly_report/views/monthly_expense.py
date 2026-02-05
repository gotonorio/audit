import logging

from common.services import select_period
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import urlencode
from django.views.generic import DeleteView, UpdateView
from record.models import AccountingClass

from monthly_report.forms import MonthlyReportExpenseForm
from monthly_report.models import ReportTransaction
from monthly_report.services.monthly_report_services import get_monthly_report_queryset

from .base import MonthlyReportBaseView
from .monthly_income import MonthlyIncomeDeleteByYearMonthView

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
        qs = get_monthly_report_queryset(tstart, tend, ac_class, "expense", is_chonaikai)

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
                "ac_class": self.object.himoku.accounting_class.id,
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
# Monthly_expense DeleteView
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
                "ac_class": self.object.himoku.accounting_class.id,
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


class MonthlyExpenseDeleteByYearMonthView(MonthlyIncomeDeleteByYearMonthView):
    """指定された年月の支出データを一括削除するFormView"""

    # 支出データ用の上書き
    title = "月次支出データの一括削除"
    return_base_url = "monthly_report:expenselist"
    income_flg = False


# ----------------------------------------------------------------------------
# 月次支出データの一括削除用 FormView
# ----------------------------------------------------------------------------
# class MonthlyExpenseDeleteByYearMonthView(MonthlyReportBaseView, PermissionRequiredMixin, FormView):
#     """指定された年月の支出データを一括削除するFormView"""

#     template_name = "monthly_report/monthly_report_delete_by_yearmonth.html"
#     form_class = DeleteByYearMonthAcclass
#     # 収入データ（支出データは下記を調整する）
#     success_url = reverse_lazy("monthly_report:expenselist")  # 削除後にリダイレクトする先
#     income_flg = False

#     def post(self, request, *args, **kwargs):
#         form = self.get_form()
#         if form.is_valid():
#             year = form.cleaned_data["year"]
#             month = form.cleaned_data["month"]
#             ac_class = form.cleaned_data["ac_class"]

#             # 1.「実行ボタン」が押された場合のみ削除
#             if "execute_delete" in request.POST or request.POST.get("execute_delete") == "true":
#                 count = ReportTransaction.delete_by_yearmonth(
#                     year, month, ac_class, is_income=self.income_flg
#                 )
#                 messages.success(request, f"{year}年{month}月のデータを {count} 件削除しました。")
#                 return redirect(self.get_success_url())

#             # 2.「確認ボタン」が押された場合は、データを抽出して同じページを表示
#             filters = {
#                 "transaction_date__year": year,
#                 "transaction_date__month": month,
#                 "himoku__is_income": self.income_flg,
#                 "amount__gt": 0,
#             }
#             if ac_class:
#                 filters["accounting_class"] = ac_class

#             target_data = ReportTransaction.objects.filter(**filters)

#             # 3. レスポンス（ac_classのNoneチェックを入れる）
#             return self.render_to_response(
#                 self.get_context_data(
#                     form=form,
#                     target_data=target_data,
#                     confirm_mode=True,
#                     year=year,
#                     month=month,
#                     # ac_classがNoneの場合の安全な処理
#                     ac_class_pk=ac_class.pk if ac_class else "",
#                     ac_class_name=ac_class.accounting_name if ac_class else "全会計区分",
#                     title="月次支出データの一括削除",
#                 )
#             )

#         return self.form_invalid(form)
