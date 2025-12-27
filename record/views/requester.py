import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views import generic

from record.forms import (
    RequesterForm,
)
from record.models import (
    TransferRequester,
)

logger = logging.getLogger(__name__)
user = get_user_model()


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
        context["requester_list"] = TransferRequester.objects.all().order_by("requester")
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
        context["requester_list"] = TransferRequester.objects.all().order_by("requester")
        return context
