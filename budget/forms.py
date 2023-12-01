from django import forms
from django.conf import settings

from budget.models import ExpenseBudget
from record.models import Himoku, AccountingClass


class Budget_listForm(forms.Form):
    """予算実績一覧表示用Form"""

    year = forms.IntegerField(
        label="西暦",
        widget=forms.NumberInput(
            attrs={
                "class": "input is-size-7",
                "style": "width:9ch",
            }
        ),
    )
    month = forms.ChoiceField(
        choices=settings.MONTH,
        widget=forms.Select(
            attrs={
                "class": "select-css is-size-7",
                "style": "width:10ch",
            }
        ),
        required=True,
    )
    kind = forms.ChoiceField(
        choices=(
            (0, "入出金明細"),
            (1, "月次報告"),
        ),
        widget=forms.Select(
            attrs={
                "class": "select-css is-size-7",
                "style": "width:12ch",
            }
        ),
    )


class BudgetExpenseForm(forms.ModelForm):
    """支出予算の入力Form
    - 支出費目は__init__()で動的に変更する。
    """

    class Meta:
        model = ExpenseBudget
        fields = (
            "year",
            "himoku",
            "budget_expense",
            "comment",
        )
        widgets = {
            "budget_expense": forms.NumberInput(
                attrs={
                    "class": "input",
                }
            ),
            "comment": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        # 先にsuper()を呼び出すと、Viewクラスで追加したac_classが存在しないエラーとなる。
        ac_class_name = kwargs.pop("ac_class")
        # ac_classを取り出した後にsuper()を呼び出す。
        super().__init__(*args, **kwargs)
        # 費目の選択要素をac_class_nameでfilterする。
        self.fields["himoku"].queryset = Himoku.objects.filter(
            accounting_class__accounting_name=ac_class_name
        )
        self.fields["himoku"].widget.attrs["class"] = "select-css"
        self.fields["himoku"].label = "支出費目選択"


class DuplicateBudgetForm(forms.Form):
    source_year = forms.IntegerField(label="複製元の年")
    target_year = forms.IntegerField(label="複製する年")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source_year"].widget.attrs["class"] = "input"
        self.fields["target_year"].widget.attrs["class"] = "input"
