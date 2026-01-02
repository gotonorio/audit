import csv
import logging
from io import TextIOWrapper

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import generic

from record.forms import (
    HimokuCsvFileSelectForm,
    HimokuForm,
    HimokuListForm,
)
from record.models import (
    Himoku,
)

logger = logging.getLogger(__name__)
user = get_user_model()


class HimokuListView(PermissionRequiredMixin, generic.TemplateView):
    """費目データ一覧表示"""

    model = Himoku
    template_name = "record/himoku_list.html"
    permission_required = "record.add_transaction"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ac_class_id = self.request.GET.get("accounting_class")

        # request.GET を渡すことで、選択した値がフォームに保持（バインド）される
        # 何も選ばれていない場合は、initial が適用される
        # form = HimokuListForm(self.request.GET or None)
        # Formに初期値を設定する
        form = HimokuListForm(initial={"accounting_class": ac_class_id})

        # フィルタリング条件の判定
        # "0" を明示的に ALL としている場合も含めて判定
        if not ac_class_id or ac_class_id == "0":
            # ac_class_id が None, "", 0, "0" のいずれかなら全件取得
            qs = Himoku.objects.all().order_by("-alive", "-is_default", "code")
        else:
            # ID（数値）が入っている場合のみフィルタリング
            qs = Himoku.objects.all().filter(accounting_class=ac_class_id).order_by("-alive", "code")

        context["himoku_list"] = qs
        context["form"] = form
        return context


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
            "-is_default",
            "-alive",
            "code",
            "-is_approval",
            "-aggregate_flag",
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
        # ログの記録
        msg = f"費目コード:{code} 費目名:{name} 会計区分:{accounting_class} を追加。by {user}"
        logger.info(msg)
        self.object.save()
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
        self.object.save()
        return super().form_valid(form)


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
        context["help_text1"] = (
            "「csvデータ」はヘッダ無しのutf-8で「会計区分名」「費目コード」「費目名」の3列データです。"
        )
        context["help_text2"] = "「会計区分名」は管理画面で登録した名前です。"
        context["help_text3"] = "「費目コード」は費目表示の並び順で使われます。"
        context["help_text4"] = "「費目名」はKuraselで設定した名前にしてください。"
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
