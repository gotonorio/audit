import logging

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic
from passbook.utils import select_period

from record.forms import ClaimListForm, ClaimUpdateForm
from record.models import ClaimData

logger = logging.getLogger(__name__)


class ClaimDataListView(PermissionRequiredMixin, generic.TemplateView):
    """管理費等請求データ一覧表示"""

    template_name = "record/claim_list.html"
    permission_required = "record.view_transaction"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = localtime(timezone.now())
        year = self.request.GET.get("year") or now.year
        month = self.request.GET.get("month") or now.month
        # 最初に表示された時はNoneなので、デフォルト値として"未収金"を設定する
        claim_type = self.request.GET.get("claim_type") or settings.RECIVABLE

        year = int(year)
        month = int(month)
        claim_type = str(claim_type)

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


class ClaimdataUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """請求時点データのUpdateView"""

    model = ClaimData
    form_class = ClaimUpdateForm
    template_name = "record/claim_update_form.html"
    permission_required = "record.add_transaction"
    raise_exception = True
    success_url = reverse_lazy("record:claim_list")

    # 保存が成功した場合に遷移するurl
    def get_success_url(self):
        qs = ClaimData.objects.filter(pk=self.object.pk).values("claim_date", "claim_type")
        year = qs[0]["claim_date"].year
        month = qs[0]["claim_date"].month
        claim_type = qs[0]["claim_type"]
        return reverse_lazy(
            "record:claim_list",
            kwargs={"year": year, "month": month, "claim_type": claim_type},
        )
