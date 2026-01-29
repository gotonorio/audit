from django import forms
from passbook.forms import YearMonthForm
from record.models import AccountingClass, Himoku

from budget.models import ExpenseBudget


# class Budget_listForm(forms.Form):
class Budget_listForm(YearMonthForm):
    """予算実績一覧表示用Form
    navbarでbulmaのselect要素を使用する場合、Djangoでclass属性を設定せずに
    HTMLテンプレート側で直接class属性を指定する。
    """

    ac_class = forms.ModelChoiceField(
        label="会計区分",
        required=False,
        queryset=AccountingClass.objects.order_by("code"),
        empty_label="会計区分を選択",
    )
    kind = forms.ChoiceField(
        choices=(
            (0, "月次報告"),
            (1, "入出金明細"),
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
            "comment": forms.Textarea(
                attrs={
                    "class": "textarea",
                    "rows": 10,
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
        ).filter(is_income=False)
        self.fields["himoku"].widget.attrs["class"] = "select-css"
        self.fields["himoku"].label = "支出費目選択"


class DuplicateBudgetForm(forms.Form):
    source_year = forms.IntegerField(label="複製元の年")
    target_year = forms.IntegerField(label="複製する年")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source_year"].widget.attrs["class"] = "input"
        self.fields["target_year"].widget.attrs["class"] = "input"
