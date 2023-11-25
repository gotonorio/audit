from django import forms
from control.models import ControlRecord


class UpdateControlForm(forms.ModelForm):
    """仮登録メニューの表示/非表示を設定"""

    class Meta:
        model = ControlRecord
        fields = ("tmp_user_flg", "annual_management_fee", "annual_greenspace_fee",)
        labels = {
            "tmp_user_flg": "仮登録表示",
            "annual_management_fee": "管理費年間収入額",
            "annual_greenspace_fee": "緑地維持管理費年間収入額",
        }
        widgets = {
            "tmp_user_flg": forms.NullBooleanSelect(attrs={"class": "select-css",}),
            "annual_management_fee": forms.NumberInput(attrs={"class": "input",}),
            "annual_greenspace_fee": forms.NumberInput(attrs={"class": "input",}),
        }
        # widgets = {
        #     'tmp_user_flg': forms.CheckboxInput(attrs={
        #         'class': 'checkbox',
        #     }),
        # }
