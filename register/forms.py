from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from django.contrib.auth.models import Group


User = get_user_model()


class LoginForm(AuthenticationForm):
    """ログインフォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input is-size-6"
            field.widget.attrs["placeholder"] = field.label


class TempUserCreateForm(UserCreationForm):
    """ユーザー仮登録用フォーム
    emailを必須フィールドにするため、UserCreationFormを継承する。
    元々はusername、password1、確認用のpassword2の3つだけど、emailを必須とする。
    https://docs.djangoproject.com/ja/3.2/topics/auth/default/
    """

    username = forms.CharField(label="ユーザ名", help_text="* 部屋番号が分かる名前にしてください。")
    email = forms.EmailField(label="Eメールアドレス", required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"


class UserUpdateForm(forms.ModelForm):
    """管理者が仮ユーザーのis_activeフラグを更新するフォーム"""

    group = forms.ModelChoiceField(
        empty_label="Group選択",
        queryset=Group.objects.all(),
        required=True,
        widget=forms.Select(attrs={"class": "select-css"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "is_active")
        labels = {
            "username": "ユーザ名",
            "is_active": "有効",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": "input"}),
            "email": forms.EmailInput(attrs={"class": "input"}),
            "is_active": forms.NullBooleanSelect(attrs={"class": "select-css"}),
        }


class PasswordUpdateForm(PasswordChangeForm):
    """ユーザーが自分のパスワードを更新するためのフォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"
