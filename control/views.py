import logging

# register/views.py
from common.services import run_database_backup
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import generic

from control.forms import UpdateControlForm
from control.models import ControlRecord

logger = logging.getLogger(__name__)


class ControlRecordListView(PermissionRequiredMixin, generic.ListView):
    model = ControlRecord
    template_name = "control/control_list.html"
    permission_required = "register.add_user"


class ControlRecordUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """コントロールデータのアップデート"""

    model = ControlRecord
    form_class = UpdateControlForm
    template_name = "control/control_form.html"
    permission_required = "register.add_user"
    # 保存が成功した場合に遷移するurl
    success_url = reverse_lazy("register:mypage")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "コントロールデータの修正"
        return context


def backupDB(request):
    """DBのバックアップ処理（View層）"""

    # サービス実行
    success, message = run_database_backup(request.user.username)

    # メッセージの振り分け
    if success:
        messages.info(request, message)
    else:
        messages.error(request, message)

    return redirect("register:master_page")
