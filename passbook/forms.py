from django import forms
from django.conf import settings


class YearMonthForm(forms.Form):
    """年月を指定するベースForm"""

    year = forms.IntegerField(
        label="西暦",
        widget=forms.NumberInput(
            attrs={
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
        self.fields["year"].widget.attrs["class"] = "input is-size-7"
        self.fields["month"].widget.attrs["class"] = "select-css is-size-7"
