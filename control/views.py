import datetime
import logging
import os
import shutil
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, reverse
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
    """DBのバックアップ処理
    静的ページに戻さざるを得ない？
    """
    # バックアップ元のDB
    db_name = settings.DATABASES["default"]["NAME"]
    _, file_ext = os.path.splitext(db_name)
    if file_ext != ".sqlite3":
        messages.info(request, "バックアップはsqlite3だけです。")
        return redirect("register:master_page")
    # バックアップ先のDB
    now = datetime.datetime.now()
    # フルパスからファイル名だけを取り出す。
    db_basename = os.path.basename(db_name)
    backup_db_name = f"{now.year}-{now.month}-{now.day}-{now.hour}-{now.minute}-({request.user})_{db_basename}"
    backup_path = f"./backupDB/{backup_db_name}"

    # バックアップ処理
    try:
        shutil.copy(db_name, backup_path)
        # https://docs.djangoproject.com/en/4.0/ref/contrib/messages/
        messages.info(request, f"DBをバックアップしました。 ファイル名:{backup_db_name}")
    except:
        messages.error(request, "バックアップに失敗しました。")

    # backupファイルが20を超えたら古いバックアップを削除する。
    # backupファイルのリスト
    file_list = os.listdir("./backupDB")
    if len(file_list) >= settings.BACKUP_NUM:
        file_list.sort()
        # ソートした結果の最初（古い）ファイルを削除する。
        os.remove("./backupDB/" + file_list[0])

    return redirect("register:master_page")
