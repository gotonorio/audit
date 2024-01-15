import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic

from monthly_report.forms import (
    BalanceSheetForm,
    BalanceSheetItemForm,
    MonthlyReportExpenseForm,
    MonthlyReportIncomeForm,
)
from monthly_report.models import BalanceSheet, BalanceSheetItem, ReportTransaction

logger = logging.getLogger(__name__)


class MonthlyReportIncomeCreateView(PermissionRequiredMixin, generic.CreateView):
    """月次報告 収入データ登録用View"""

    model = ReportTransaction
    form_class = MonthlyReportIncomeForm
    template_name = "monthly_report/monthly_report_form.html"
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("monthly_report:create_income")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "月次報告 収入データの登録/編集"
        return context

    def form_valid(self, form):
        # commitを停止する。
        self.object = form.save(commit=False)
        # # transaction_dateを YYYY-MM-01に強制的に修正する。
        # self.object.transaction_date = self.object.transaction_date.replace(day=1)
        # authorをセット。
        self.object.author = self.request.user
        self.object.created_date = timezone.now()
        # データを保存。
        self.object.save()
        # messages.success(self.request, "保存しました。")
        return super().form_valid(form)


class MonthlyReportExpenseCreateView(MonthlyReportIncomeCreateView):
    """月次報告 支出データ登録用View
    MonthlyReportIncomeCreateViewを継承する。
    """

    form_class = MonthlyReportExpenseForm
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("monthly_report:create_expense")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "月次報告 支出データの登録/編集"
        return context

    def form_valid(self, form):
        # commitを停止する。
        self.object = form.save(commit=False)
        # # transaction_dateを YYYY-MM-01に強制的に修正する。
        # self.object.transaction_date = self.object.transaction_date.replace(day=1)
        # authorをセット。
        self.object.author = self.request.user
        self.object.created_date = timezone.now()
        # データを保存。
        self.object.save()
        # messages.success(self.request, "保存しました。")
        return super().form_valid(form)


class MonthlyReportIncomeUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """月次報告 収入データアップデートView"""

    model = ReportTransaction
    form_class = MonthlyReportIncomeForm
    template_name = "monthly_report/monthly_report_form.html"
    permission_required = "record.add_transaction"

    # 保存が成功した場合に遷移するurl
    def get_success_url(self):
        # qs = ReportTransaction.objects.filter(pk=self.object.pk).values_list('transaction_date', flat=True)
        # year = qs[0].year
        # month = qs[0].month
        # return reverse_lazy('monthly_report:incomelist', kwargs={'year': year, 'month': month})
        qs = ReportTransaction.objects.filter(pk=self.object.pk).values(
            "transaction_date", "accounting_class"
        )
        year = qs[0]["transaction_date"].year
        month = qs[0]["transaction_date"].month
        ac_class = qs[0]["accounting_class"]
        return reverse_lazy(
            "monthly_report:incomelist",
            kwargs={"year": year, "month": month, "ac_class": ac_class},
        )

    def form_valid(self, form):
        # commitを停止する。
        self.object = form.save(commit=False)
        # # transaction_dateを YYYY-MM-01に強制的に修正する。
        # self.object.transaction_date = self.object.transaction_date.replace(day=1)
        # updated_dateをセット。
        self.object.author = self.request.user
        self.object.created_date = timezone.now()
        # データを保存。
        self.object.save()
        # messages.success(self.request, "保存しました。")
        return super().form_valid(form)


class MonthlyReportExpenseUpdateView(MonthlyReportIncomeUpdateView):
    """月次報告 支出データアップデートView"""

    form_class = MonthlyReportExpenseForm

    # 保存が成功した場合に遷移するurl
    def get_success_url(self):
        qs = ReportTransaction.objects.filter(pk=self.object.pk).values(
            "transaction_date", "accounting_class"
        )
        year = qs[0]["transaction_date"].year
        month = qs[0]["transaction_date"].month
        ac_class = qs[0]["accounting_class"]
        return reverse_lazy(
            "monthly_report:expenselist",
            kwargs={"year": year, "month": month, "ac_class": ac_class},
        )

    def form_valid(self, form):
        # commitを停止する。
        self.object = form.save(commit=False)
        # # transaction_dateを YYYY-MM-01に強制的に修正する。
        # self.object.transaction_date = self.object.transaction_date.replace(day=1)
        # updated_dateをセット。
        self.object.author = self.request.user
        self.object.created_date = timezone.now()
        # データを保存。
        self.object.save()
        # messages.success(self.request, "保存しました。")
        return super().form_valid(form)


class DeleteIncomeView(PermissionRequiredMixin, generic.DeleteView):
    """月次報告収入データ削除View"""

    model = ReportTransaction
    template_name = "monthly_report/reporttransaction_confirm_delete.html"
    permission_required = "record.add_transaction"
    # success_url = reverse_lazy('register:mypage')

    def get_success_url(self):
        obj = self.object
        qs = ReportTransaction.objects.filter(pk=obj.pk).values("transaction_date", "accounting_class")
        year = qs[0]["transaction_date"].year
        month = qs[0]["transaction_date"].month
        ac_class = qs[0]["accounting_class"]
        return reverse_lazy(
            "monthly_report:incomelist", kwargs={"year": year, "month": month, "ac_class": ac_class}
        )


class DeleteExpenseView(DeleteIncomeView):
    """月次報告支出データ削除View"""

    def get_success_url(self):
        qs = ReportTransaction.objects.filter(pk=self.object.pk).values(
            "transaction_date", "accounting_class"
        )
        year = qs[0]["transaction_date"].year
        month = qs[0]["transaction_date"].month
        ac_class = qs[0]["accounting_class"]
        return reverse_lazy(
            "monthly_report:expenselist",
            kwargs={"year": year, "month": month, "ac_class": ac_class},
        )


class BalanceSheetCreateView(PermissionRequiredMixin, generic.CreateView):
    """貸借対照表の未収金・前受金・未払金のCreateView"""

    model = BalanceSheet
    form_class = BalanceSheetForm
    template_name = "monthly_report/bs_form.html"
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("monthly_report:create_bs")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = localtime(timezone.now()).year
        context["bs_list"] = BalanceSheet.objects.filter(monthly_date__contains=year).order_by(
            "-monthly_date", "item_name"
        )
        return context


class BalanceSheetUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """貸借対照表の未収金・前受金・未払金のUpdateView"""

    model = BalanceSheet
    form_class = BalanceSheetForm
    template_name = "monthly_report/bs_form.html"
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True

    # 保存が成功した場合に遷移するurl
    def get_success_url(self):
        # 取り込みに成功したら、貸借対照表を表示する。
        qs = BalanceSheet.objects.filter(pk=self.object.pk).first()
        year = qs.monthly_date.year
        month = qs.monthly_date.month
        ac_class = qs.item_name.ac_class.pk

        return reverse_lazy(
            "monthly_report:bs_table",
            kwargs={"year": year, "month": month, "ac_class": ac_class},
        )


class BalanceSheetDeleteView(PermissionRequiredMixin, generic.DeleteView):
    """貸借対照表データの削除処理"""

    model = BalanceSheet
    template_name = "monthly_report/bs_delete_confirm.html"
    permission_required = "record.add_transaction"
    success_url = reverse_lazy("monthly_report:create_bs")


class BalanceSheetItemCreateView(PermissionRequiredMixin, generic.CreateView):
    """貸借対照表の科目データの作成"""

    model = BalanceSheetItem
    form_class = BalanceSheetItemForm
    template_name = "monthly_report/bs_item_form.html"
    permission_required = "record.add_transaction"
    raise_exception = True
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("monthly_report:create_bs_item")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bs_item_list"] = BalanceSheetItem.objects.all().order_by("code", "is_asset")
        return context


class BalanceSheetItemUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """貸借対照表の科目データのアップデート"""

    model = BalanceSheetItem
    form_class = BalanceSheetItemForm
    template_name = "monthly_report/bs_item_form.html"
    permission_required = "record.add_transaction"
    raise_exception = True
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("monthly_report:create_bs_item")
