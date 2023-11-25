from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import redirect, resolve_url
from django.urls import reverse_lazy
from django.views import generic

from register.forms import PasswordUpdateForm, TempUserCreateForm, UserUpdateForm

User = get_user_model()


class UserListView(PermissionRequiredMixin, generic.ListView):
    """管理者が使用するユーザリストの一覧表示。
    templatesファイルはデフォルト（user_list.html）を使用。
    渡されるobjectもデフォルトの「user_list」。
    """

    model = User
    template_name = "register/user/user_list.html"
    permission_required = ("register.add_user",)

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs).order_by("is_active")
        qs = qs.exclude(is_superuser=True).order_by("-groups", "is_active")
        return qs


class TempUserCreateView(generic.CreateView):
    """未登録ユーザーが仮登録するためのVIEW。
    ユーザには「add_post」と「view_post」のパーミションを付加する。
    """

    template_name = "register/user/create_temp_user_form.html"
    form_class = TempUserCreateForm

    def form_valid(self, form):
        """仮登録ではis_activeフラグを立てず、管理者が承認することで
        is_active=Trueとする。また登録するユーザには権限を付加する。
        """
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        return redirect("register:done_temp_user")


class TempUserDoneView(generic.TemplateView):
    """仮登録完了後、メールを待つように表示するだけのVIEW。"""

    template_name = "register/user/done_temp_user.html"


class OnlyYouMixin(UserPassesTestMixin):
    """パスワードの変更処理用
    自分自身だけでなく、ユーザ登録情報によって制限することができる。
    https://qiita.com/chanyou0311/items/31a4380d11c904563c86
    https://docs.djangoproject.com/ja/3.2/topics/auth/default/
    """

    raise_exception = True

    def test_func(self):
        user = self.request.user
        # return user.pk == self.kwargs['pk'] or user.is_superuser
        return user.pk == self.kwargs["pk"]


class UserPasswordUpdate(OnlyYouMixin, PasswordChangeView):
    """ログインしたユーザが自分でパスワードを変更するためのVIEW。"""

    model = User
    form_class = PasswordUpdateForm
    template_name = "register/user/update_password_form.html"

    def get_success_url(self):
        # return resolve_url('register:pwd_update', pk=self.kwargs['pk'])
        return resolve_url("register:mypage")


class UserManagementView(PermissionRequiredMixin, generic.UpdateView):
    """管理者がユーザの「有効性」を操作するためのVIEW。"""

    model = User
    form_class = UserUpdateForm
    template_name = "register/user/update_user_form.html"
    permission_required = ("register.add_user",)

    def get_success_url(self):
        return resolve_url("register:user_list")

    def form_valid(self, form):
        """仮登録ではis_activeフラグを立てず、管理者が承認することで
        is_active=Trueとする。またグループの変更も行う。
        """
        user = form.save(commit=False)
        user.save()
        new_group = form.cleaned_data["group"]
        user.groups.clear()
        group = Group.objects.get(name=new_group)
        user.groups.add(group)
        return redirect("register:user_list")

    def get_context_data(self, **kwargs):
        """ユーザ修正画面で現在値をformに表示させる"""
        context = super().get_context_data(**kwargs)
        pk = self.object.pk
        user = User.objects.get(pk=pk)
        groups = user.groups.all()
        if groups.exists():
            group_name = groups[0]
        else:
            group_name = ""

        update_user_form = UserUpdateForm(
            initial={
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "group": group_name,
            }
        )
        context["form"] = update_user_form
        return context


class DeleteUserView(PermissionRequiredMixin, generic.DeleteView):
    """削除View"""

    model = User
    # 削除が成功した場合に遷移するurl
    success_url = reverse_lazy("register:user_list")
    # 削除してよいか確認するためのtemplate
    template_name = "register/user/delete_user_confirm.html"
    # 必要な権限（データ登録できる権限は共通）
    permission_required = ("register.add_user",)
    # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
    raise_exception = True
