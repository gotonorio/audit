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


class CreateKanriBudgetView(PermissionRequiredMixin, generic.CreateView):
    """支出予算の登録用View"""

    model = ExpenseBudget
    form_class = BudgetExpenseForm
    template_name = "budget/budget_form.html"
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("budget:create_budget")

    def get_form_kwargs(self, *args, **kwargs):
        """Formクラスへ値(accounting_class名)を渡す
        - https://hideharaaws.hatenablog.com/entry/2017/02/05/021111
        - https://itc.tokyo/django/get-form-kwargs/
        - 管理費会計、修繕積立金会計、駐車場会計、町内会会計
        """
        kwargs = super().get_form_kwargs(*args, **kwargs)
        # 管理会計区分名をkwargsに追加する。
        ac_class_name = AccountingClass.get_class_name("管理")
        kwargs["ac_class"] = ac_class_name
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # # 支出予算
        # qs_budget = (ExpenseBudget.objects.filter(year=year).order_by("himoku__code"))
        context["title"] = "支出予算の登録/編集"
        # context["budget"] = qs_budget
        return context


class CreateShuuzenBudgetView(CreateKanriBudgetView):
    """修繕積立金会計の支出予算の登録用View
    - CreateKanriBudgetViewを継承する。
    """

    success_url = reverse_lazy("budget:create_shuuzen_budget")

    def get_form_kwargs(self, *args, **kwargs):
        """Formクラスへ値(accounting_class名)を渡す
        - https://hideharaaws.hatenablog.com/entry/2017/02/05/021111
        - https://itc.tokyo/django/get-form-kwargs/
        - 管理費会計、修繕積立金会計、駐車場会計、町内会会計
        """
        kwargs = super().get_form_kwargs(*args, **kwargs)
        # 管理会計区分名をkwargsに追加する。
        ac_class_name = AccountingClass.get_class_name("修繕")
        kwargs["ac_class"] = ac_class_name
        return kwargs


class CreateParkingBudgetView(CreateKanriBudgetView):
    """駐車場会計の支出予算の登録用View
    - CreateKanriBudgetViewを継承する。
    """

    success_url = reverse_lazy("budget:create_parking_budget")

    def get_form_kwargs(self, *args, **kwargs):
        """Formクラスへ値(accounting_class名)を渡す
        - https://hideharaaws.hatenablog.com/entry/2017/02/05/021111
        - https://itc.tokyo/django/get-form-kwargs/
        - 管理費会計、修繕積立金会計、駐車場会計、町内会会計
        """
        kwargs = super().get_form_kwargs(*args, **kwargs)
        # 管理会計区分名をkwargsに追加する。
        ac_class_name = AccountingClass.get_class_name("駐車")
        kwargs["ac_class"] = ac_class_name
        return kwargs


class UpdateBudgetView(PermissionRequiredMixin, generic.UpdateView):
    """支出予算のアップデートView"""

    model = ExpenseBudget
    form_class = BudgetExpenseForm
    template_name = "budget/budget_form.html"
    permission_required = "record.add_transaction"
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("budget:budget_update_list")

    def get_form_kwargs(self, *args, **kwargs):
        """Formで必要なため、kwargsに「accounting_class名」を渡す
        - https://hideharaaws.hatenablog.com/entry/2017/02/05/021111
        - https://itc.tokyo/django/get-form-kwargs/
        - 管理費会計、修繕積立金会計、駐車場会計、町内会会計
        """
        kwargs = super().get_form_kwargs(*args, **kwargs)
        # 会計区分名をkwargsに追加する。
        pk = self.kwargs.get("pk")
        ac_class_name = ExpenseBudget.objects.get(pk=pk).himoku.accounting_class
        kwargs["ac_class"] = ac_class_name
        return kwargs


class UpdateBudgetListView(PermissionRequiredMixin, generic.ListView):
    """管理会計予算の修正用リスト表示処理"""

    model = ExpenseBudget
    template_name = "budget/update_budget_list.html"
    permission_required = "record.add_transaction"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(self.request.GET.get("year", localtime(timezone.now()).year))
        ac_class = self.request.GET.get("ac_class", 1)
        # 支出予算
        qs = ExpenseBudget.objects.filter(year=year).filter(himoku__alive=True)
        qs = qs.filter(himoku__accounting_class=ac_class).order_by("himoku__code")
        if qs is None:
            messages.info(self.request, "予算が作成されていないようです。")
            return context

        # 予算合計（年間）
        total_qs = qs.aggregate(Sum("budget_expense"))
        total_budget = total_qs["budget_expense__sum"]

        ### 以下は管理会計の場合だけ、予算オーバのチェックを行う
        class_name = AccountingClass.get_accountingclass_name(ac_class)
        if class_name == "管理費会計":
            # 管理会計収入額（年間）
            income_qs = ControlRecord.objects.values("annual_management_fee", "annual_greenspace_fee")
            annual_income = 0
            if income_qs:
                annual_income = income_qs[0]["annual_management_fee"] + income_qs[0]["annual_greenspace_fee"]
            if total_budget - annual_income > 0:
                messages.info(self.request, f"予算({annual_income}円)をオーバーしています。")
            context["annual_income"] = annual_income

        # forms.pyのKeikakuListFormに初期値を設定する
        form = Budget_listForm(
            initial={
                "year": year,
                "ac_class": ac_class,
            }
        )
        ki = year - 1998
        context["title"] = f"{year}年 第{ki}期 管理会計予算"
        context["form"] = form
        context["budget"] = qs
        context["total"] = total_budget
        return context


class DuplicateBudgetView(PermissionRequiredMixin, generic.FormView):
    """年次（複製）処理
    - 複製する必要があるのは管理会計予算のみ。
    """

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
        qs = qs.filter(himoku__accounting_class__accounting_name=kanriclass_name).order_by("himoku__code")
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
        else:
            # 複製を作成
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
    # # 4.0以降delete()をオーバライドするのではなく、form_valid()をオーバライドするようだ。
    # # https://docs.djangoproject.com/ja/4.0/ref/class-based-views/generic-editing/#deleteview
    # def form_valid(self, form):
    #     logger.warning("delete Budget費目:{}:{}".format(self.request.user, self.object))
    #     return super().form_valid(form)

    def delete(self, request, *args, **kwargs):
        # 削除対象のオブジェクトを取得
        obj = self.get_object()
        # ログの記録
        logger.info(f"delete Budget費目:{self.request.user}:{obj}")
        # オブジェクトを削除
        response = super().delete(request, *args, **kwargs)
        # メッセージの表示（任意）
        messages.success(self.request, "Object successfully deleted.")

        return response
