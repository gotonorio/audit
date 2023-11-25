import csv
import logging
from io import TextIOWrapper

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic
from django.views.generic.edit import FormView

from record.forms import (
    AccountTitleForm,
    HimokuCsvFileSelectForm,
    HimokuForm,
    RequesterForm,
    TransactionCreateForm,
    TransactionDivideForm,
    TransactionDivideFormSet,
    TransactionOffsetForm,
)
from record.models import Account, Himoku, Transaction, TransferRequester

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

    def form_valid(self, form):
        # commitを停止する。
        self.object = form.save(commit=False)
        # authorをセット。
        self.object.author = self.request.user
        # 入力した日時をセット。
        self.object.created_date = timezone.now()
        # データを保存。
        self.object.save()
        # messages.success(self.request, "保存しました。")
        return super().form_valid(form)


class TransactionUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """取引明細 UpdateView"""

    model = Transaction
    form_class = TransactionCreateForm
    template_name = "record/transaction_form.html"
    permission_required = "record.add_transaction"

    # 保存が成功した場合に遷移するurl
    def get_success_url(self):
        qs = Transaction.objects.filter(pk=self.object.pk).values_list(
            "transaction_date", flat=True
        )
        year = qs[0].year
        month = qs[0].month
        # UPDATE後の会計区分は「全会計区分」を表示させる。
        ac_class = 0
        list_order = 0
        return reverse_lazy(
            "record:transaction_list",
            kwargs={
                "year": year,
                "month": month,
                "ac_class": ac_class,
                "list_order": list_order,
            },
        )

    def form_valid(self, form):
        # commitを停止する。
        self.object = form.save(commit=False)
        # updated_dateをセット。
        self.object.author = self.request.user
        self.object.created_date = timezone.now()
        # データを保存。
        self.object.save()
        # messages.success(self.request, "保存しました。")
        return super().form_valid(form)


class TransactionDeleteView(PermissionRequiredMixin, generic.DeleteView):
    """取引明細 DeleteView"""

    model = Transaction
    permission_required = "record.add_transaction"

    # 削除が成功した場合に遷移するurlを返す。
    def get_success_url(self):
        qs = Transaction.objects.filter(pk=self.object.pk).values_list(
            "transaction_date", flat=True
        )
        year = qs[0].year
        month = qs[0].month
        return reverse_lazy(
            "record:transaction_list",
            kwargs={"year": year, "month": month, "ac_class": 0, "list_order": 0},
        )

    # 4.0以降delete()をオーバライドするのではなく、form_valid()をオーバライドするようだ。
    # https://docs.djangoproject.com/ja/4.0/ref/class-based-views/generic-editing/#deleteview
    def form_valid(self, form):
        logger.warning(
            "delete {}:{}:{}:{}".format(
                self.request.user,
                self.object.transaction_date,
                self.object,
                self.object.ammount,
            )
        )
        return super().form_valid(form)


class HimokuCreateView(PermissionRequiredMixin, generic.CreateView):
    """費目マスタ CreateView"""

    model = Himoku
    form_class = HimokuForm
    template_name = "record/himoku_form.html"
    permission_required = "record.add_transaction"
    raise_exception = True
    success_url = reverse_lazy("record:himoku_create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["himoku_list"] = Himoku.objects.all().order_by(
            "-alive", "-is_approval", "-aggregate_flag", "code"
        )
        return context

    def form_valid(self, form):
        """費目マスタデータの追加ログを記録する"""
        # commitを停止する。
        self.object = form.save(commit=False)
        user = self.request.user
        code = form.cleaned_data["code"]
        name = form.cleaned_data["himoku_name"]
        accounting_class = form.cleaned_data["accounting_class"]
        # log message
        msg = f"費目コード:{code} 費目名:{name} 会計区分:{accounting_class} を追加。by {user}"
        logger.info(msg)
        return super().form_valid(form)


class HimokuUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """費目マスタ UpdateView"""

    model = Himoku
    form_class = HimokuForm
    template_name = "record/himoku_form.html"
    permission_required = "record.add_transaction"
    raise_exception = True
    success_url = reverse_lazy("record:himoku_create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["himoku_list"] = Himoku.objects.all().order_by("code")
        return context

    def form_valid(self, form):
        """費目マスタデータの修正ログを記録する"""
        # commitを停止する。
        self.object = form.save(commit=False)
        user = self.request.user
        code = form.cleaned_data["code"]
        name = form.cleaned_data["himoku_name"]
        accounting_class = form.cleaned_data["accounting_class"]
        # log message
        msg = f"費目コード:{code} 費目名:{name} 会計区分:{accounting_class}に修正。by {user}"
        logger.info(msg)
        return super().form_valid(form)


class TransferRequesterCreateView(PermissionRequiredMixin, generic.CreateView):
    """振込依頼者 CreateView"""

    model = TransferRequester
    form_class = RequesterForm
    template_name = "record/requester_form.html"
    permission_required = "record.add_transaction"
    raise_exception = True
    success_url = reverse_lazy("record:requester_create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["requester_list"] = TransferRequester.objects.all().order_by(
            "requester"
        )
        return context


class TransferRequesterUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """振込依頼者 UpdateView"""

    model = TransferRequester
    form_class = RequesterForm
    template_name = "record/requester_form.html"
    permission_required = "record.add_transaction"
    raise_exception = True
    success_url = reverse_lazy("record:requester_create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["requester_list"] = TransferRequester.objects.all().order_by(
            "requester"
        )
        return context


class TransactionOffsetCreateView(PermissionRequiredMixin, generic.TemplateView):
    """入出金明細データの相殺レコード作成
    - 相殺データを作成した後、作成したレコードのpkをTransactionDivideCreateView()へ
      送るためにTemplateViewを使う。
    - formはTransactionCreateFormを利用。
    - templateは不要な項目を表示しないように新規に作成。
    """

    template_name = "record/transaction_offset_form.html"
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            pk = kwargs["pk"]
            # 相殺する元データを読み込む
            qs = Transaction.objects.get(pk=pk)
            # formに初期値をセット
            form = TransactionOffsetForm(
                initial={
                    "account": qs.account,
                    "is_manualinput": True,
                    "calc_flg": True,
                    "transaction_date": qs.transaction_date,
                    "ammount": (qs.ammount * -1),
                    "requesters_name": f"{qs.requesters_name}(相殺)",
                    "description": qs.description,
                    "himoku": qs.himoku,
                    "balance": qs.balance,
                }
            )
        context["form"] = form

        return context

    def post(self, request, *args, **kwargs):
        form = TransactionOffsetForm(request.POST)
        if form.is_valid():
            # formオブジェクトから年、月を読み込む。
            year = form.cleaned_data["transaction_date"].year
            month = form.cleaned_data["transaction_date"].month
            # 新しく保存されたオブジェクトのpkはsave関数の戻り値で得られる。
            offset_pk = form.save()
            return redirect("record:transaction_divide", pk=offset_pk.pk)
        else:
            return self.render_to_response({"form": form})


class TransactionDivideCreateView(PermissionRequiredMixin, FormView):
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
        user_id = self.request.user.id
        # 分割元のデータpk
        pk = self.kwargs.get("pk")
        # デフォルト値の設定
        qs = Transaction.objects.get(pk=pk)
        transaction_date = qs.transaction_date
        balance = qs.balance
        himoku = Himoku.objects.get(himoku_name="不明")

        # formにはformsetがセットされているので、繰り返し処理する。
        for subform in form:
            ammount = subform.cleaned_data.get("ammount")
            if ammount is not None and int(ammount) > 0:
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
                    divide.is_icome = False
                    # 費目名は「不明」に決め打ち
                    divide.himoku = himoku
                    # 金額、、振込依頼人、摘要はFormから受け取る
                    divide.ammount = ammount
                    divide.requesters_name = requesters_name
                    divide.description = description
                    divide.author = user.objects.get(id=user_id)
                    divide.is_manualinput = True
                    divide.calc_flg = True
                    divide.save()
                except Exception as e:
                    logger.error(e)
                    error_list.append(divide)
                    return self.render_to_response(self.get_context_data(form=form))

        # 保存が成功したら入出金明細にredirectする。
        year = transaction_date.year
        month = transaction_date.month
        return redirect(
            "record:transaction_list", year=year, month=month, ac_class=0, list_order=0
        )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class HimokuCsvReadView(PermissionRequiredMixin, generic.FormView):
    """費目マスタをCSVファイルから読み込む。
    modelクラスとの連携が必要ないのでFormViewで処理する。
    """

    template_name = "record/read_himoku_csv.html"
    form_class = HimokuCsvFileSelectForm
    # 読み込みが成功したら遷移するurl。
    success_url = reverse_lazy("record:himoku_create")
    # 必要な権限
    permission_required = "record.add_transaction"
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True
    rc_list = []
    rc_file_name = ""

    def get_context_data(self, **kwargs):
        """このViewがGETで呼ばれた時、テンプレートに変数を渡す。"""
        context = super().get_context_data(**kwargs)
        context["title"] = "費目マスタCSVファイルの読み込み"
        context["help_text"] = "※ csvデータはヘッダ無し。"
        return context

    def csv_to_list(self, form):
        """csvファイルを読み込んでlistとして返す"""
        # 選択されたcsvファイルオブジェクト
        csvfile = form.cleaned_data["file"]
        # 表示のためにファイル名を保持しておく。
        self.rc_file_name = csvfile
        # CSVデータをパースしてリストに格納
        himoku_list = list(csv.reader(TextIOWrapper(csvfile.file, "utf-8")))
        return himoku_list

    def form_valid(self, form):
        """csvファイルで読み込んだ費目マスタをDBに登録する"""
        # 費目マスタを読み込んでListに変換する。
        himoku_list = self.csv_to_list(form)

        # 費目マスタの登録
        if len(himoku_list) > 0:
            rtn, error_list = Himoku.save_himoku(himoku_list)

        return redirect("record:himoku_create")
