from django import forms

from control.models import ControlRecord


class UpdateControlForm(forms.ModelForm):
    """仮登録メニューの表示/非表示を設定"""

    class Meta:
        model = ControlRecord
        fields = (
            "tmp_user_flg",
            "annual_management_fee",
            "annual_greenspace_fee",
            "to_offset",
            "delete_data_flg",
        )
        labels = {
            "tmp_user_flg": "仮登録メニュー表示",
            "annual_management_fee": "管理費年間収入額",
            "annual_greenspace_fee": "緑地維持管理費年間収入額",
            "to_offset": "相殺する費目",
            "delete_data_flg": "データ削除フラグ表示",
        }
        widgets = {
            "tmp_user_flg": forms.NullBooleanSelect(
                attrs={
                    "class": "select-css",
                }
            ),
            "annual_management_fee": forms.NumberInput(
                attrs={
                    "class": "input",
                }
            ),
            "annual_greenspace_fee": forms.NumberInput(
                attrs={
                    "class": "input",
                }
            ),
            "to_offset": forms.Select(
                attrs={
                    "class": "select-css",
                }
            ),
            "delete_data_flg": forms.NullBooleanSelect(
                attrs={
                    "class": "select-css",
                }
            ),
        }
        help_texts = {
            "tmp_user_flg": "※ 仮登録メニューを表示するかどうかを設定する。",
            "annual_management_fee": "※ 予算実績対比表で予算チェックのため。",
            "annual_greenspace_fee": "※ 予算実績対比表で予算チェックのため。",
            "to_offset": "※ 相殺する費目を登録。",
            "delete_data_flg": "※ データ削除フラグの表示/非表示を設定する。",
        }
