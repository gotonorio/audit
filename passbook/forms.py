from django import forms
from django.conf import settings


class YearMonthForm(forms.Form):
    """年月を指定するベースForm
    - navbarでの使用にclassを設定。その他での使用時は__init__()を上書き指定する。
    """

    year = forms.IntegerField(
        label="西暦",
        min_value=2000,
        max_value=2200,
        widget=forms.NumberInput(
            attrs={
                "class": "input is-small",  # デフォルトで navbar 仕様にしておく
                "style": "width:10ch",
            }
        ),
    )
    month = forms.ChoiceField(
        label="月",
        choices=[(i, f"{i}月") for i in range(1, 13)],
        widget=forms.Select(
            attrs={
                "style": "width:10ch",
            }
        ),
    )

    # navbar以外でformを使う場合、__init__()を上書きしてclass属性を調整する。
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields["year"].widget.attrs["class"] = "input"
        # self.fields["month"].widget.attrs["class"] = "select-css"


class YearMonthALLForm(YearMonthForm):
    """全月を選択肢に指定するベースForm"""

    month = forms.ChoiceField(
        label="月",
        widget=forms.Select(
            attrs={
                "style": "width:10ch",
            }
        ),
        choices=[(0, "ALL")] + [(i, f"{i}月") for i in range(1, 13)],
    )
