import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from record.forms import TransactionCreateForm
from record.models import Transaction

logger = logging.getLogger(__name__)
user = get_user_model()


class TransactionCreateView(PermissionRequiredMixin, generic.CreateView):
    """取引明細登録用 CreateView"""

    model = Transaction
    form_class = TransactionCreateForm
    template_name = "record/transaction_form.html"
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("record:transaction_create")

    # TransactionCreateFormに変数（値）を渡す
    #    def get_form_kwargs(self, *args, **kwargs):
    #        """formクラスでは以下のようにkwargsからpopする。
    #        __init__(self, *args, **kwargs):
    #            self.create_flag = kwargs.pop('create_flag')
    #            super().__init__(*args, **kwargs)
    #        """
    #        kwgs = super().get_form_kwargs(*args, **kwargs)
    #        kwgs["create_flag"] = True
    #        return kwgs

    def get_context_data(self, **kwargs):
        """templateファイルに変数を渡す"""
        context = super().get_context_data(**kwargs)
        # ここで変数を追加
        context["form_title"] = "入出金明細データの手動作成"
        return context

    def form_valid(self, form):
        # commitを停止する。
        self.object = form.save(commit=False)
        # authorをセット。
        self.object.author = self.request.user
        # 入力した日時をセット。
        self.object.created_date = timezone.now()
        # ログの記録
        msg = (
            f"日付「{self.object.created_date.date()}」"
            f"費目名「{self.object.himoku}」"
            f"金額「{self.object.amount:,}」"
            f"作成者「{self.request.user}」"
        )
        logger.info(msg)
        # データを保存。
        self.object.save()
        messages.success(self.request, "保存しました。")
        return super().form_valid(form)


class TransactionUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """取引明細 UpdateView"""

    model = Transaction
    form_class = TransactionCreateForm
    template_name = "record/transaction_form.html"
    permission_required = "record.add_transaction"

    # TransactionCreateFormに変数（値）を渡す
    #    def get_form_kwargs(self, *args, **kwargs):
    #        """formクラスでは以下のようにkwargsからpopする。
    #        __init__(self, *args, **kwargs):
    #            self.create_flag = kwargs.pop('create_flag')
    #            super().__init__(*args, **kwargs)
    #        """
    #        kwgs = super().get_form_kwargs(*args, **kwargs)
    #        kwgs["create_flag"] = False
    #        return kwgs

    # 保存が成功した場合に遷移するurl
    def get_success_url(self):
        qs = Transaction.objects.filter(pk=self.object.pk).values_list("transaction_date", flat=True)
        year = qs[0].year
        month = qs[0].month
        # UPDATE後に表示する時の「year」「month」「list_order」「himoku_id」をkwargsに設定。
        return reverse_lazy(
            "record:transaction_list",
            kwargs={"year": year, "month": month, "list_order": 0, "himoku_id": 0},
        )

    def get_context_data(self, **kwargs):
        """templateファイルに変数を渡す"""
        context = super().get_context_data(**kwargs)
        # ここで変数を追加
        context["form_title"] = "入出金明細データの修正"
        return context

    def form_valid(self, form):
        # commitを停止する。
        self.object = form.save(commit=False)
        # updated_dateをセット。
        self.object.author = self.request.user
        self.object.created_date = timezone.now()
        # ログの記録
        msg = (
            f"日付「{self.object.created_date.date()}」"
            f"費目名「{self.object.himoku}」"
            f"金額「{self.object.amount:,}」"
            f"作成者「{self.request.user}」"
        )
        logger.info(msg)
        # データを保存。
        self.object.save()
        messages.success(self.request, "修正しました。")
        return super().form_valid(form)


class TransactionDeleteView(PermissionRequiredMixin, generic.DeleteView):
    """取引明細 DeleteView"""

    model = Transaction
    permission_required = "record.add_transaction"

    # 削除が成功した場合の遷移処理
    def get_success_url(self):
        qs = Transaction.objects.filter(pk=self.object.pk).values_list("transaction_date", flat=True)
        year = qs[0].year
        month = qs[0].month
        return reverse_lazy(
            "record:transaction_list",
            kwargs={"year": year, "month": month, "list_order": 0, "himoku_id": 0},
        )

    def form_valid(self, form):
        """djang 4.0で、delete()で行う処理はform_valid()を使うようになったみたい。
        https://stackoverflow.com/questions/53145279/edit-record-before-delete-django-deleteview
        https://docs.djangoproject.com/ja/4.0/ref/class-based-views/generic-editing/#deleteview
        """
        # ログに削除の情報を記録する
        msg = (
            f"削除 日付「{self.object.transaction_date}」"
            f"費目「{self.object.himoku}」"
            f"金額「{self.object.amount:,}」"
            f"摘要「{self.object.description}」"
            f"削除者「{self.request.user}」"
        )
        logger.info(msg)
        # メッセージ表示
        messages.success(self.request, "削除しました。")
        return super().form_valid(form)
