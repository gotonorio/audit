from django import forms
from django.conf import settings

from budget.models import ExpenseBudget
from record.models import Himoku


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
    """支出予算の入力Form"""

    # 項目を絞るためquerysetを上書きする
    himoku = forms.ModelChoiceField(
        label="支出費目選択",
        required=True,
        queryset=Himoku.objects.filter(alive=True, is_income=False).order_by("code"),
        widget=forms.Select(attrs={"class": "select-css is-size-6"}),
    )

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
        # help_texts = {
        #     'transaction_date': '* 不明な日付は01日とする。',
        #     'calc_flg': '前払金の振替や不測の現金収入などはチェックを外す。',
        #     }


class DuplicateBudgetForm(forms.Form):
    source_year = forms.IntegerField(label="複製元の年")
    target_year = forms.IntegerField(label="複製する年")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source_year"].widget.attrs["class"] = "input"
        self.fields["target_year"].widget.attrs["class"] = "input"
