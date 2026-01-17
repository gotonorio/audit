import logging

from common.services import select_period
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic

from record.forms import TransactionDisplayForm
from record.models import Transaction

logger = logging.getLogger(__name__)


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
