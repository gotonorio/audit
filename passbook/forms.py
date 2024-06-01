from django import forms

MONTH = (
    ("1", "1月"),
    ("2", "2月"),
    ("3", "3月"),
    ("4", "4月"),
    ("5", "5月"),
    ("6", "6月"),
    ("7", "7月"),
    ("8", "8月"),
    ("9", "9月"),
    ("10", "10月"),
    ("11", "11月"),
    ("12", "12月"),
)


class YearMonthForm(forms.Form):
    """年月を指定するベースForm"""

    year = forms.IntegerField(
        label="西暦",
        widget=forms.NumberInput(
            attrs={
                "style": "width:9ch",
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
        choices=MONTH,
        required=True,
    )
