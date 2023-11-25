# from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from explanation.forms import DescriptionCreateForm, DescriptionListForm
from explanation.models import Description


class DescriptionView(LoginRequiredMixin, generic.TemplateView):
    """プログラムの説明文表示"""

    model = Description
    template_name = "explanation/description.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.request.GET.get("title", False)
        if pk == "" or pk is False:
            qs = None
        else:
            qs = Description.objects.get(pk=pk)

        form = DescriptionListForm(
            initial={
                "title": pk,
            }
        )
        context["qs"] = qs
        context["form"] = form
        return context


class DescriptionCreateView(PermissionRequiredMixin, generic.CreateView):
    """説明文モデルを作成"""

    model = Description
    form_class = DescriptionCreateForm
    permission_required = ("record.add_transaction",)
    template_name = "explanation/description_form.html"
    success_url = reverse_lazy("register:mypage")


class DescriptionUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """説明文モデルのアップデート"""

    model = Description
    form_class = DescriptionCreateForm
    permission_required = ("record.add_transaction",)
    template_name = "explanation/description_form.html"
    success_url = reverse_lazy("register:mypage")
