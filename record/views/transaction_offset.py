import logging

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.views import generic

from record.forms import (
    TransactionDivideFormSet,
    TransactionOffsetForm,
)
from record.models import Transaction
from record.services.transaction import (
    create_divided_transactions,
    create_offset_transaction,
)

logger = logging.getLogger(__name__)


class TransactionOffsetCreateView(PermissionRequiredMixin, generic.TemplateView):
    """入出金明細データの相殺レコード作成（入出金明細データ一覧で「ソウゴウフリコミBIZ」を分解する時に呼ばれる）
    - 相殺データを作成した後、作成したレコードのpkをTransactionDivideCreateView()へ送るためにTemplateViewを使う。
    - templateは不要な項目を表示しないように新規に作成。
    1. GETリクエスト時：相殺データの初期値をセットしたフォームを表示（kwargsでpkを受け取る）
    2. POSTリクエスト時：相殺データを保存し、分割画面へリダイレクト
    参考：https://docs.djangoproject.com/en/4.2/topics/class-based-views/generic-display/#templateview
    """

    template_name = "record/transaction_offset_form.html"
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            pk = self.kwargs["pk"]
            # 相殺する元データを読み込む
            qs = Transaction.objects.get(pk=pk)
            # formに初期値をセット
            # form = TransactionCreateForm(
            form = TransactionOffsetForm(
                initial={
                    "account": qs.account,
                    "is_income": qs.is_income,
                    "is_manualinput": True,
                    "calc_flg": True,
                    "transaction_date": qs.transaction_date,
                    "amount": (qs.amount * -1),
                    "requesters_name": f"{qs.requesters_name}",
                    "description": f"{qs.description}（相殺）",
                    "himoku": qs.himoku,
                    "balance": qs.balance,
                }
            )
            context["form"] = form
        return context

    def post(self, request, *args, **kwargs):
        """登録ボタンが押された時の処理"""
        base = Transaction.objects.get(pk=self.kwargs["pk"])

        offset = create_offset_transaction(
            base_transaction=base,
            user=request.user,
        )

        # 新しく保存されたオブジェクトのpkはsave関数の戻り値で得られる。
        return redirect("record:transaction_divide", pk=offset.pk)


class TransactionDivideCreateView(PermissionRequiredMixin, generic.FormView):
    """分割した出金レコードの保存
    - FormViewを使うメリット:https://en-junior.com/form_view_post/
    - 一般的にform_validからの遷移はsuccess_urlかget_success_urlを使うが、
        parameterの関係でform_validからredirect関数で遷移させる。
    """

    template_name = "record/transaction_divide_form.html"
    permission_required = "record.add_transaction"

    # 分割したレコード（データ）を複数同時に入力・保存するためFormSetを使う。
    # FormSetを使う場合、form_classではなくget_form_classをオーバーライドする。
    def get_form_class(self):
        # 実行時にFormSetクラスを返す
        return TransactionDivideFormSet

    def get_context_data(self, **kwargs):
        """相殺処理されたレコードを表示する"""
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        qs = Transaction.objects.get(pk=pk)
        formset = TransactionDivideFormSet()
        context["qs"] = qs
        context["formset"] = formset
        return context

    def form_valid(self, form):
        base = Transaction.objects.get(pk=self.kwargs["pk"])

        try:
            create_divided_transactions(
                base_transaction=base,
                divide_forms=form,
                user=self.request.user,
            )
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.render_to_response(self.get_context_data(form=form))

        year = base.transaction_date.year
        month = base.transaction_date.month
        return redirect("record:transaction_list", year=year, month=month, list_order=0, himoku_id=0)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))
