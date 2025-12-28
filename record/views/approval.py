import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views import generic

from record.forms import ApprovalCheckDataForm
from record.models import ApprovalCheckData

logger = logging.getLogger(__name__)
user = get_user_model()


class ApprovalTextCreateView(PermissionRequiredMixin, generic.CreateView):
    """入出金データの適用欄のテキストで支払い承認が必要かどうかを判定するためのデータを登録する"""

    model = ApprovalCheckData
    form_class = ApprovalCheckDataForm
    template_name = "record/approval_text_form.html"
    permission_required = "record.add_transaction"
    raise_exception = True
    success_url = reverse_lazy("record:approval_text_create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["approval_text_list"] = ApprovalCheckData.objects.all()
        return context


class ApprovalTextUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """入出金データの適用欄のテキストで支払い承認が必要かどうかを判定するためのデータを編集する"""

    model = ApprovalCheckData
    form_class = ApprovalCheckDataForm
    template_name = "record/approval_text_form.html"
    permission_required = "record.add_transaction"
    raise_exception = True
    success_url = reverse_lazy("record:approval_text_create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["approval_text_list"] = ApprovalCheckData.objects.all()
        return context
