import logging

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.aggregates import Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic

from budget.forms import Budget_listForm, BudgetExpenseForm, DuplicateBudgetForm
from budget.models import ExpenseBudget
from control.models import ControlRecord
from record.models import AccountingClass


logger = logging.getLogger(__name__)


class CreateBudgetView(PermissionRequiredMixin, generic.CreateView):
    """支出予算の登録用View"""

    model = ExpenseBudget
    form_class = BudgetExpenseForm
    template_name = "budget/budget_form.html"
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("budget:create_budget")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = localtime(timezone.now()).year
        # 支出予算
        qs_budget = ExpenseBudget.objects.filter(year=year).order_by("himoku__code")

        context["title"] = "支出予算の登録/編集"
        context["budget"] = qs_budget
        return context


class UpdateBudgetView(PermissionRequiredMixin, generic.UpdateView):
    """支出予算のアップデートView"""

    model = ExpenseBudget
    form_class = BudgetExpenseForm
    template_name = "budget/budget_form.html"
    permission_required = "record.add_transaction"
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("budget:budget_update_list")


class UpdateBudgetListView(PermissionRequiredMixin, generic.ListView):
    """管理会計予算の修正用リスト表示処理"""

    model = ExpenseBudget
    template_name = "budget/update_budget_list.html"
    permission_required = "record.add_transaction"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(self.request.GET.get("year", localtime(timezone.now()).year))
        # 支出予算
        qs = ExpenseBudget.objects.filter(year=year).filter(himoku__alive=True)
        # 管理会計区分のみとしてfilterする。
        kanriclass_name = AccountingClass.get_class_name("管理")
        qs = qs.filter(
            himoku__accounting_class__accounting_name=kanriclass_name
        ).order_by("himoku__code")
        # 予算合計（年間）
        total_qs = qs.aggregate(Sum("budget_expense"))
        total_budget = total_qs["budget_expense__sum"]
        # 管理会計収入額（年間）
        income_qs = ControlRecord.objects.values(
            "annual_management_fee", "annual_greenspace_fee"
        )
        if income_qs:
            annual_income = (
                income_qs[0]["annual_management_fee"]
                + income_qs[0]["annual_greenspace_fee"]
            )
        if total_budget - annual_income > 0:
            messages.info(self.request, f"予算({annual_income}円)をオーバーしています。")
        # forms.pyのKeikakuListFormに初期値を設定する
        form = Budget_listForm(
            initial={
                "year": year,
            }
        )
        ki = year - 1998
        context["title"] = f"{year}年 第{ki}期 管理会計予算"
        context["form"] = form
        context["budget"] = qs
        context["total"] = total_budget
        context["annual_income"] = annual_income
        return context


class DuplicateBudgetView(PermissionRequiredMixin, generic.FormView):
    """年次（複製）処理"""

    template_name = "budget/duplicate_budget.html"
    form_class = DuplicateBudgetForm
    # 必要な権限
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。
    raise_exception = True
    success_url = reverse_lazy("budget:budget_update_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(self.request.GET.get("year", localtime(timezone.now()).year))
        # 現在の予算を表示させる。
        qs = ExpenseBudget.objects.filter(year=year).filter(himoku__alive=True)
        # 管理会計区分のみとしてfilterする。
        kanriclass_name = AccountingClass.get_class_name("管理")
        qs = qs.filter(
            himoku__accounting_class__accounting_name=kanriclass_name
        ).order_by("himoku__code")
        # formフィールドに初期値を設定。
        form = DuplicateBudgetForm(
            initial={
                "source_year": year,
                "target_year": year + 1,
            }
        )
        context["list"] = qs
        context["form"] = form
        return context

    def post(self, request, *args, **kwargs):
        """データを一括生成する"""
        source_year = self.request.POST.get("source_year", False)
        target_year = self.request.POST.get("target_year", False)
        # もしtarget_yearのデータが存在したら複製処理は中止する。
        is_exist = ExpenseBudget.objects.all().filter(year=target_year).exists()
        if is_exist:
            msg = f"{target_year}年のデータは存在します。"
            messages.info(request, msg)
            redirect("budget:budget_update_list")
        # 最新の予算データ
        qs = ExpenseBudget.objects.all().filter(year=source_year)
        new_budget = []
        for d in qs:
            budget = ExpenseBudget(
                year=target_year,
                himoku=d.himoku,
                budget_expense=d.budget_expense,
                comment=d.comment,
            )
            new_budget.append(budget)
        ExpenseBudget.objects.bulk_create(new_budget)
        return redirect(self.get_success_url())


class DeleteBudgetView(PermissionRequiredMixin, generic.DeleteView):
    """年間予算費目の削除処理"""

    model = ExpenseBudget
    template_name = "budget/delete_confirm.html"
    permission_required = "record.add_transaction"
    success_url = reverse_lazy("budget:budget_update_list")

    # 削除処理をログ出力する。
    # 4.0以降delete()をオーバライドするのではなく、form_valid()をオーバライドするようだ。
    # https://docs.djangoproject.com/ja/4.0/ref/class-based-views/generic-editing/#deleteview
    def form_valid(self, form):
        logger.warning("delete Budget費目:{}:{}".format(self.request.user, self.object))
        return super().form_valid(form)
