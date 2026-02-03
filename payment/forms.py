from django import forms
from django.conf import settings
from passbook.forms import YearMonthForm
from record.models import Himoku

from payment.models import Payment, PaymentMethod


# -----------------------------------------------------------------------------
# データ表示用Form
# -----------------------------------------------------------------------------
class ApprovalPaymentListForm(YearMonthForm):
    """支払い承認データ表示用Form"""

    # 全月表示のためYearMonthFormを上書きする
    month = forms.ChoiceField(
        label="月",
        choices=[(0, "ALL")] + settings.MONTH,
        # select の装飾は Bulma に任せ、widget 側は素の select にする。基本的には削除しておく。
        widget=forms.Select(attrs={"class": ""}),
    )
    # YearMonthFormに日付項目を追加
    day = forms.ChoiceField(
        label="日",
        choices=(
            ("00", "ALL"),
            ("10", "10日支払い"),
            ("25", "25日支払い"),
        ),
        required=True,
    )
    # 費目順表示フラグ
    list_order = forms.ChoiceField(
        label="費目順",
        choices=(
            (0, "日付順"),
            (1, "費目順"),
        ),
        required=True,
    )


# -----------------------------------------------------------------------------
# データ登録用Form
# -----------------------------------------------------------------------------
class ApprovalPaymentCreateForm(forms.ModelForm):
    """支払い承認データ登録・編集用フォーム"""

    himoku = forms.ModelChoiceField(
        label="費目選択",
        required=False,
        queryset=Himoku.objects.filter(alive=True, is_income=False, code__lt=9000).order_by("code"),
        widget=forms.Select(attrs={"class": "select-css"}),
    )

    class Meta:
        model = Payment
        fields = [
            "himoku",
            "payment_date",
            "payment_destination",
            "payment",
            "summary",
        ]
        widgets = {
            "payment_destination": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
            "payment": forms.NumberInput(
                attrs={
                    "class": "input",
                }
            ),
            "summary": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
            "payment_date": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
        }
        help_texts = {
            "summary": "* 町内会会計では摘要の修正をしないでください。",
        }


class MonthYearSelectionForm(YearMonthForm):
    """支払い承認データの削除用フォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["year"].widget.attrs["class"] = "input"
        self.fields["month"].widget.attrs["class"] = "select-css"


class PaymentMethodCreateForm(forms.ModelForm):
    """支払い方法の追加作成"""

    # 支出費目名だけを表示するため
    himoku_name = forms.ModelChoiceField(
        label="費目名",
        queryset=Himoku.objects.filter(is_income=False).order_by("code"),
        widget=forms.Select(
            attrs={
                "class": "select-css",
            }
        ),
    )

    class Meta:
        model = PaymentMethod
        fields = [
            "ac_class",
            "payment_category",
            "himoku_name",
            "payee",
            "amounts",
            "banking_fee",
            "account_description",
            "comment",
        ]
        widgets = {
            "ac_class": forms.Select(
                attrs={
                    "class": "select-css",
                }
            ),
            "payment_category": forms.Select(
                attrs={
                    "class": "select-css",
                }
            ),
            "payee": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
            "amounts": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
            "banking_fee": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
            "account_description": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "text",
                    "rows": 5,
                    "cols": 54,
                }
            ),
        }
        help_texts = {
            "account_description": "※ カナは「全角カナ」とすること。",
        }
