# import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views import generic

from control.models import ControlRecord
from register.forms import LoginForm

User = get_user_model()


class Login(LoginView):
    """ログインページ"""

    form_class = LoginForm
    template_name = "register/login.html"

    def get_context_data(self, **kwargs):
        """ログインページで仮登録メニューを表示させる"""
        context = super().get_context_data(**kwargs)
        qs = ControlRecord.objects.values("tmp_user_flg")
        if qs:
            context["tmp_user_flg"] = qs[0]["tmp_user_flg"]
        return context


class Logout(LoginRequiredMixin, LogoutView):
    """ログアウトページ"""

    template_name = "register/logout.html"


class MypageView(LoginRequiredMixin, generic.TemplateView):
    """mobileとPCでトップ画面を分ける -> 2023-08-04 mobile対応は停止"""

    def get_template_names(self):
        """templateファイルを切り替える"""
        if self.request.user_agent_flag == "mobile":
            template_name = "register/mypage_pc.html"
        else:
            template_name = "register/mypage_pc.html"
        return [template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context["user_id"] = self.request.user.id
        return context


class MasterPageView(LoginRequiredMixin, generic.TemplateView):
    template_name = "register/master_page.html"
