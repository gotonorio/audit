from django import forms
from django.conf import settings

from payment.models import Payment, PaymentMethod
from record.models import Himoku


class ApprovalPaymentListForm(forms.Form):
    """支払い承認データ表示用Form"""

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
        label="月",
        widget=forms.Select(
            attrs={
                "class": "select-css is-size-7",
                "style": "width:10ch",
            }
        ),
        choices=settings.MONTH_ALL,
        required=True,
    )
    day = forms.ChoiceField(
        label="日",
        widget=forms.Select(
            attrs={
                "class": "select-css is-size-7",
                "style": "width:10ch",
            }
        ),
        choices=(
            ("00", "ALL"),
            ("10", "10日支払い"),
            ("25", "25日支払い"),
        ),
        required=True,
    )


class ApprovalPaymentCreateForm(forms.ModelForm):
    """支払い承認データ登録・編集用フォーム"""

    himoku = forms.ModelChoiceField(
        label="費目選択",
        required=False,
        queryset=Himoku.objects.filter(alive=True).filter(is_income=False, alive=True).order_by("code"),
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
