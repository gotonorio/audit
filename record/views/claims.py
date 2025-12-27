import logging

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from passbook.utils import select_period

from record.forms import ClaimListForm
from record.models import ClaimData

logger = logging.getLogger(__name__)


class ClaimDataListView(PermissionRequiredMixin, generic.TemplateView):
    """管理費等請求データ一覧表示"""

    template_name = "record/claim_list.html"
    permission_required = "record.view_transaction"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if kwargs:
            year = self.kwargs["year"]
            month = self.kwargs["month"]
            claim_type = str(self.kwargs["claim_type"])
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
