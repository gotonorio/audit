import logging

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from passbook.utils import select_period
from record.forms import (
    ClaimListForm,
    TransactionDisplayForm,
)
from record.models import ClaimData, Transaction

logger = logging.getLogger(__name__)


class TransactionListView(PermissionRequiredMixin, generic.TemplateView):
    """細目別に分割した入出金明細リスト月別表示
    - 全月が選択された場合、摘要で並べ替える。2022/04/28
    - 細目別に分割した補正データを表示する処理を追加。2023-08-21
    """

    model = Transaction
    template_name = "record/transaction_list.html"
    permission_required = ("record.view_transaction",)
    # Kuraselオリジナルか補正データを表示するかのフラグとしてクラス変数is_manualを定義する。
    is_manual = True
    # 資金移動（すまい・る債）の入出金も表示するが合計には含めない
    is_calc_flg = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 入出金データの「読込み・修正」が成功した場合にDepositWithdrawalVie()でwkwargsがセットされる。
        if kwargs:
            year = kwargs["year"]
            month = kwargs["month"]
            list_order = str(kwargs["list_order"])
            himoku_id = kwargs["himoku_id"]
        else:
            local_now = localtime(timezone.now())
            year = self.request.GET.get("year", local_now.year)
            month = self.request.GET.get("month", local_now.month)
            list_order = self.request.GET.get("list_order", "0")
            himoku_id = self.request.GET.get("himoku_id", 0)

        # 抽出期間
        tstart, tend = select_period(year, month)

        # リストの作成。（補正データ、計算フラグOFFも表示する）
        qs = Transaction.get_qs_pb(tstart, tend, "0", "0", "", self.is_manual, self.is_calc_flg)
        if himoku_id and int(himoku_id) > 0:
            qs = qs.filter(himoku=himoku_id)

        # 表示順序
        if list_order == "0":
            qs = qs.order_by(
                "-transaction_date",
                "himoku__himoku_name",
                "is_manualinput",
                "is_income",
                "requesters_name",
            )
        else:
            qs = qs.order_by("himoku__himoku_name", "-transaction_date", "requesters_name")
        # Kuraselの入出金明細データの合計
        total_deposit, total_withdrawals = Transaction.total_all(qs)
        # forms.pyのKeikakuListFormに初期値を設定する
        form = TransactionDisplayForm(
            initial={
                "year": year,
                "month": month,
                "list_order": list_order,
                "himoku_id": himoku_id,
            }
        )
        context["transaction_list"] = qs
        context["form"] = form
        context["total_deposit"] = total_deposit
        context["total_withdrawals"] = total_withdrawals
        context["total_balance"] = total_deposit - total_withdrawals
        context["year"] = year
        context["month"] = month
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
        tstart, tend = select_period(year, 0)
        # 期間と前受金フラグでfiler
        qs = (
            Transaction.objects.all()
            .select_related("account")
            .filter(transaction_date__range=[tstart, tend])
            .filter(is_maeukekin=True)
        )
        form = TransactionDisplayForm(
            initial={
                "year": year,
            }
        )
        context["chk_obj"] = qs
        context["form"] = form
        return context


class ClaimDataListView(PermissionRequiredMixin, generic.TemplateView):
    """管理費等請求データ一覧表示"""

    template_name = "record/claim_list.html"
    permission_required = "record.view_transaction"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            year = kwargs["year"]
            month = kwargs["month"]
            claim_type = str(kwargs["claim_type"])
        else:
            local_now = localtime(timezone.now())
            year = self.request.GET.get("year", local_now.year)
            month = self.request.GET.get("month", local_now.month)
            # 最初に表示された時はNoneなので、デフォルト値として"未収金"を設定する
            claim_type = self.request.GET.get("claim_type", settings.RECIVABLE)
        # claim_list.htmlのタイトル
        if claim_type in (settings.RECIVABLE, settings.MAEUKE):
            title = "「請求時点」の" + claim_type
        else:
            title = claim_type
        # 抽出期間
        tstart, tend = select_period(year, month)
        # querysetの作成。
        claim_qs, claim_total = ClaimData.get_claim_list(tstart, tend, claim_type)
        # Formに初期値を設定する
        form = ClaimListForm(initial={"year": year, "month": month, "claim_type": claim_type})
        context["claim_list"] = claim_qs
        context["claim_total"] = claim_total
        context["form"] = form
        context["title"] = title
        context["yyyymm"] = str(year) + "年" + str(month) + "月"
        return context
