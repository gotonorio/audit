import logging

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views import generic

from record.forms import (
    TransactionDivideFormSet,
    TransactionOffsetForm,
)
from record.models import Himoku, Transaction

logger = logging.getLogger(__name__)


class TransactionOffsetCreateView(PermissionRequiredMixin, generic.TemplateView):
    """入出金明細データの相殺レコード作成（入出金明細データ一覧で「ソウゴウフリコミBIZ」を分解する時に呼ばれる）
    - 相殺データを作成した後、作成したレコードのpkをTransactionDivideCreateView()へ送るためにTemplateViewを使う。
    - templateは不要な項目を表示しないように新規に作成。
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
        form = TransactionOffsetForm(request.POST)
        if form.is_valid():
            # formオブジェクトから年、月を読み込む。
            # year = form.cleaned_data["transaction_date"].year
            # month = form.cleaned_data["transaction_date"].month
            # 新しく保存されたオブジェクトのpkはsave関数の戻り値で得られる。
            offset_pk = form.save()
            return redirect("record:transaction_divide", pk=offset_pk.pk)
        else:
            return self.render_to_response({"form": form})


class TransactionDivideCreateView(PermissionRequiredMixin, generic.FormView):
    """分割した出金レコードの保存
    - FormViewを使うメリット:https://en-junior.com/form_view_post/
    - 一般的にform_validからの遷移はsuccess_urlかget_success_urlを使うが、
        parameterの関係でform_validからredirect関数で遷移させる。
    """

    template_name = "record/transaction_divide_form.html"
    permission_required = "record.add_transaction"
    # 分割したレコード（データ）を複数同時に入力・保存するためFormSetを使う。
    form_class = TransactionDivideFormSet

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
        """分割設定したレコードを保存する。
        - 金額0は保存しない。
        """
        error_list = []
        # 分割元のデータpk
        pk = self.kwargs.get("pk")
        # デフォルト値の設定
        qs = Transaction.objects.get(pk=pk)
        transaction_date = qs.transaction_date
        balance = qs.balance
        # 分割する金額
        base_amount = -qs.amount
        # 分割した場合、費目はデフォルト費目とする
        default_himoku = Himoku.get_default_himoku()
        # 入金・出金フラグ
        is_income = qs.is_income

        # 分割したデータの合計金額をチェックする。
        total_divide_amount = 0
        for subform in form:
            if subform.cleaned_data.get("amount") is not None:
                total_divide_amount += subform.cleaned_data.get("amount")
        if total_divide_amount != base_amount:
            messages.add_message(
                self.request,
                messages.ERROR,
                f"{total_divide_amount:,} != {base_amount:,} 合計の不一致",
            )
            return self.render_to_response(self.get_context_data(form=form))

        # formにはformsetがセットされているので、繰り返し処理する。
        for subform in form:
            amount = subform.cleaned_data.get("amount")
            if amount is not None and int(amount) > 0:
                # 振込依頼人はFormから受け取る
                requesters_name = subform.cleaned_data.get("requesters_name")
                # 摘要はFormから受け取る
                description = subform.cleaned_data.get("description")
                # 保存処理
                try:
                    # instanceを作成
                    divide = Transaction()
                    # 登録されている口座は「管理会計口座」の1件だけ。
                    divide.account = Account.objects.all().first()
                    # 取引日は相殺データの日付に決め打ち
                    divide.transaction_date = transaction_date
                    # 残高
                    divide.balance = balance
                    # 登録するのは出金データのみ
                    divide.is_income = is_income
                    # 費目名は「不明」に決め打ち
                    divide.himoku = default_himoku
                    # 金額、、振込依頼人、摘要はFormから受け取る
                    divide.amount = amount
                    divide.requesters_name = requesters_name
                    divide.description = description
                    # divide.author = user.objects.get(id=user_id)
                    divide.author = self.request.user
                    divide.is_manualinput = True
                    divide.calc_flg = True
                    # ログを記録
                    msg = f"{transaction_date} : 金額:{amount:,}を作成。by {self.request.user}"
                    logger.info(msg)
                    divide.save()
                except Exception as e:
                    logger.error(e)
                    error_list.append(amount)
                    return self.render_to_response(self.get_context_data(form=form))

        # 保存が成功したら入出金明細にredirectする。
        year = transaction_date.year
        month = transaction_date.month
        return redirect("record:transaction_list", year=year, month=month, list_order=0, himoku_id=0)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))
