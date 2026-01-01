import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from passbook.utils import select_period

from record.forms import TransactionDisplayForm
from record.models import Transaction

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

        now = localtime(timezone.now())
        year = self.request.GET.get("year") or now.year
        month = self.request.GET.get("month") or now.month
        list_order = self.request.GET.get("list_order") or 0
        himoku_id = self.request.GET.get("himoku_id") or 0

        year = int(year)
        month = int(month)
        list_order = int(list_order)
        himoku_id = int(himoku_id)

        # 抽出期間
        tstart, tend = select_period(year, month)

        # リストの作成。（補正データ、計算フラグOFFも表示する）
        qs = Transaction.get_qs_pb(tstart, tend, "0", "0", "", self.is_manual, self.is_calc_flg)
        if himoku_id and int(himoku_id) > 0:
            qs = qs.filter(himoku=himoku_id)

        # 表示順序
        if list_order == 0:
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
