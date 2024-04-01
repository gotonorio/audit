import logging

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic

from kurasel_translator.my_lib.append_list import select_period
from record.forms import RecalcBalanceForm, TransactionDisplayForm
from record.models import AccountingClass, Himoku, Transaction

logger = logging.getLogger(__name__)


class TransactionListView(PermissionRequiredMixin, generic.TemplateView):
    """入出金明細リスト月別表示
    - 全月が選択された場合、摘要で並べ替える。2022/04/28
    - 補正データを表示する処理を追加。2023-08-21
    """

    model = Transaction
    template_name = "record/transaction_list.html"
    permission_required = ("record.view_transaction",)
    # Kuraselオリジナルか補正データを表示するかのフラグとしてクラス変数is_manualを定義する。
    is_manual = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # update後に元のviewに戻る処理のためkwargsを使う。TransactionUpdateViewを参照。
        if kwargs:
            year = kwargs["year"]
            month = kwargs["month"]
            # ac_class = kwargs["ac_class"]
            list_order = kwargs["list_order"]
        else:
            local_now = localtime(timezone.now())
            year = self.request.GET.get("year", local_now.year)
            month = self.request.GET.get("month", local_now.month)
            # ac_class = self.request.GET.get("ac_class", "0")
            list_order = self.request.GET.get("list_order", "0")
        # 抽出期間
        tstart, tend = select_period(year, month)

        # querysetの作成。（補正データも表示する）
        qs = Transaction.get_qs_pb(tstart, tend, "0", "0", "", self.is_manual)

        # 表示順序
        if list_order == "0":
            qs = qs.order_by("-transaction_date", "himoku", "is_manualinput", "requesters_name")
        else:
            qs = qs.order_by("himoku", "-transaction_date", "requesters_name")
        # 合計金額
        total_deposit, total_withdrawals = Transaction.all_total(qs)
        # forms.pyのKeikakuListFormに初期値を設定する
        form = TransactionDisplayForm(
            initial={
                "year": year,
                "month": month,
                # "ac_class": ac_class,
                "list_order": list_order,
            }
        )
        context["transaction_list"] = qs
        context["form"] = form
        context["total_deposit"] = total_deposit
        context["total_withdrawals"] = total_withdrawals
        context["total_balance"] = total_deposit - total_withdrawals
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        return context


class TransactionOriginalListView(TransactionListView):
    """取引明細リストのKuraselデータのみ表示"""

    # Kuraselオリジナルデータだけを表示するためクラス変数is_manualをFalseに定義する。
    template_name = "record/transaction_original_list.html"
    is_manual = False


class CheckMaeukeDataView(PermissionRequiredMixin, generic.TemplateView):
    """前受金のcalc_flgがオフになっているか確認
    - TransactionCreateForm()でバリデーョンを行うようにしたので不要のはず。
    """

    model = Transaction
    template_name = "record/chk_maeuke.html"
    permission_required = "record.add_transaction"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.GET.get("year", localtime(timezone.now()).year)
        # 抽出期間
        tstart, tend = select_period(year, "all")
        # 期間でfiler
        qs = (
            Transaction.objects.all().select_related("account").filter(transaction_date__range=[tstart, tend])
        )
        # 管理会計区分を指定する
        ac_class = AccountingClass.get_class_name("管理")
        # 費目名「前受金」でfilter
        maeukekin = Himoku.get_himoku_obj(settings.MAEUKE, ac_class)
        qs = qs.filter(himoku=maeukekin).order_by("-transaction_date")
        form = TransactionDisplayForm(
            initial={
                "year": year,
            }
        )
        context["chk_obj"] = qs
        context["form"] = form
        return context


class RecalcBalance(PermissionRequiredMixin, generic.TemplateView):
    """残高を計算する"""

    model = Transaction
    template_name = "record/recalc_balance_form.html"
    permission_required = "record.add_transaction"

    def recalc(self, qs, balance):
        rebalance = {}
        for obj in qs:
            # 入金のコードは99以下とする。
            if obj.is_income:
                balance += obj.ammount
            else:
                balance -= obj.ammount
            rebalance[obj.transaction_date] = balance
        return rebalance

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = localtime(timezone.now()).year
        start_date = str(year) + "-" + "01-01"

        # 開始日
        sdate = self.request.GET.get("sdate", start_date)
        # 残高
        balance = self.request.GET.get("balance", 0)
        # 基準日が入力されていれば、チェック開始
        if sdate != "":
            start_date = sdate.split("-")
            year = start_date[0]
            month = start_date[1]
            day = start_date[2]
            sdate = timezone.datetime(int(year), int(month), int(day), 0, 0, 0)
            # 計算は指定日の翌日分から
            tdate = sdate + timezone.timedelta(days=1)
            qs = Transaction.objects.filter(transaction_date__gte=tdate).order_by("transaction_date")
            # 残高の再計算処理
            rebalance = self.recalc(qs, int(balance))
            context["rebalance_list"] = rebalance

        # forms.pyのKeikakuListFormに初期値を設定する
        form = RecalcBalanceForm(
            initial={
                "sdate": sdate,
                "balance": balance,
            }
        )
        context["form"] = form
        return context
