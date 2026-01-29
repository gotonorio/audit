from django import forms
from django.conf import settings


class YearMonthForm(forms.Form):
    """年月を指定するベースForm
    - navbarでの使用にclassを設定。その他での使用時はclassを上書き指定する。
    """

    year = forms.IntegerField(
        label="西暦",
        widget=forms.NumberInput(
            attrs={
                "class": "input is-small",  # デフォルトで navbar 仕様にしておく
                "style": "width:10ch",
            }
        ),
    )

    month = forms.ChoiceField(
        label="月",
        widget=forms.Select(
            attrs={
                "style": "width:10ch",
            }
        ),
        choices=settings.MONTH,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields["year"].widget.attrs["class"] = "input"
        # self.fields["year"].widget.attrs["style"] = "width:10ch"
        # navbarでselect要素の設定はHTML側で行うため、class属性の設定はしない。


class YearMonthALLForm(YearMonthForm):
    """全月を選択肢に指定するベースForm"""

    month = forms.ChoiceField(
        label="月",
        widget=forms.Select(
            attrs={
                "style": "width:10ch",
            }
        ),
        choices=[(0, "ALL")] + settings.MONTH,
    )
