from django import forms
from django.conf import settings
from django.utils import timezone

from record.forms import TransactionDisplayForm
from record.models import AccountingClass, Himoku

from .models import BalanceSheet, BalanceSheetItem, ReportTransaction


#
# データ登録用Form
#
class MonthlyReportIncomeForm(forms.ModelForm):
    """月次報告収入データ編集用フォーム"""

    himoku = forms.ModelChoiceField(
        label="費目選択",
        required=False,
        queryset=Himoku.objects.filter(alive=True, is_income=True).order_by("code"),
        widget=forms.Select(attrs={"class": "select-css is-size-6"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["transaction_date"].initial = timezone.datetime.now().strftime("%Y-%m-%d")

    class Meta:
        model = ReportTransaction
        fields = [
            "account",
            "accounting_class",
            "transaction_date",
            "ammount",
            "himoku",
            "description",
            "mishuu_flg",
            "calc_flg",
        ]
        labels = {
            "transaction_date": "取引月",
            "mishuu_flg": "未収入金",
            "calc_flg": "計算フラグ",
            "description": "摘要",
        }
        widgets = {
            "account": forms.Select(
                attrs={
                    "class": "select-css",
                }
            ),
            "accounting_class": forms.Select(
                attrs={
                    "class": "select-css",
                }
            ),
            "transaction_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "is-size-6",
                }
            ),
            "ammount": forms.NumberInput(
                attrs={
                    "class": "input",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
        }
        help_texts = {
            "transaction_date": "* 不明な日付は01日とする。",
            "calc_flg": "前払金の振替や不測の現金収入などはチェックを外す。",
        }

    def clean_transaction_date(self):
        """未来の日付をチェック"""
        td = self.cleaned_data.get("transaction_date")
        # datetime.dateをdatetime.datetimeに変更して比較する。
        transaction_date = timezone.datetime(td.year, td.month, td.day, 0, 0, 0)
        today = timezone.datetime.today()
        if transaction_date > today:
            raise forms.ValidationError("未来の日付です！")
        return transaction_date


class MonthlyReportExpenseForm(MonthlyReportIncomeForm):
    """月次報告支出データ編集用フォーム himoku選択フィールドだけを変更"""

    himoku = forms.ModelChoiceField(
        label="費目選択",
        required=False,
        queryset=Himoku.objects.filter(alive=True, is_income=False).order_by("code"),
        widget=forms.Select(attrs={"class": "select-css is-size-6"}),
    )

    class Meta:
        model = ReportTransaction
        fields = [
            "account",
            "accounting_class",
            "transaction_date",
            "ammount",
            "himoku",
            "description",
            "miharai_flg",
            "calc_flg",
            "is_netting",
        ]
        labels = {
            "miharai_flg": "未払い",
        }
        widgets = {
            "account": forms.Select(
                attrs={
                    "class": "select-css",
                }
            ),
            "accounting_class": forms.Select(
                attrs={
                    "class": "select-css",
                }
            ),
            "transaction_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "value": timezone.datetime.now().strftime("%Y-%m-%d"),
                    "class": "is-size-6",
                }
            ),
            "ammount": forms.NumberInput(
                attrs={
                    "class": "input",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
        }
        help_texts = {
            "transaction_date": "* 不明な日付は01日とする。",
        }


class BalanceSheetForm(forms.ModelForm):
    """貸借対照表の未収金・前受金手動入力用Form"""

    # 項目名選択で表示順を「項目名」にするため、overrideする。
    item_name = forms.ModelChoiceField(
        label="項目名選択",
        required=True,
        queryset=BalanceSheetItem.objects.order_by("item_name"),
        widget=forms.Select(attrs={"class": "select-css is-size-6"}),
    )

    class Meta:
        model = BalanceSheet
        fields = [
            "monthly_date",
            "amounts",
            "item_name",
            "comment",
        ]
        # labels = {
        #     'item_name': '項目名',
        # }
        widgets = {
            "monthly_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "value": timezone.datetime.now().strftime("%Y-%m-%d"),
                    "class": "is-size-6",
                }
            ),
            "amounts": forms.NumberInput(
                attrs={
                    "class": "input",
                }
            ),
            # 'item_name': forms.Select(attrs={
            #     'class': 'select-css',
            # }),
            "comment": forms.Textarea(
                attrs={
                    "class": "textarea",
                    "rows": 5,
                }
            ),
        }
        help_texts = {
            "monthly_date": "* 日付は月末日とする。",
        }


class BalanceSheetItemForm(forms.ModelForm):
    """貸借対照表科目の登録・修正用Form"""

    class Meta:
        model = BalanceSheetItem
        fields = [
            "code",
            "ac_class",
            "item_name",
            "is_asset",
        ]
        widgets = {
            "code": forms.NumberInput(
                attrs={
                    "class": "is-size-6",
                }
            ),
            "ac_class": forms.Select(
                attrs={
                    "class": "select-css",
                }
            ),
            "item_name": forms.TextInput(
                attrs={
                    "class": "is-size-6",
                }
            ),
        }


#
# データ表示用Form
#
class MonthlyReportViewForm(TransactionDisplayForm):
    """月次報告の収入リスト表示用Form"""

    accounting_class = forms.ModelChoiceField(
        label="会計区分",
        required=False,
        queryset=AccountingClass.objects.order_by("code"),
        empty_label="会計区分ALL",
        widget=forms.Select(attrs={"class": "select-css is-size-7"}),
    )


class YearReportChoiceForm(forms.Form):
    """月次報告の年間一覧表示用Form"""

    year = forms.IntegerField(
        label="西暦",
        widget=forms.NumberInput(
            attrs={
                "class": "input is-size-7",
                "style": "width:9ch",
            }
        ),
    )
    accounting_class = forms.ModelChoiceField(
        queryset=AccountingClass.objects.all().order_by("code"),
        label="会計区分",
        empty_label="会計区分ALL",
        required=False,
        widget=forms.Select(attrs={"class": "select-css is-size-7"}),
    )


class BalanceSheetTableForm(forms.Form):
    """貸借対照表の表示用Form"""

    year = forms.IntegerField(
        label="西暦",
        initial=2023,
        widget=forms.NumberInput(
            attrs={
                "class": "input is-size-7",
                "style": "width:10ch",
            }
        ),
    )
    # settings.MONTHから最初の要素を除去する。
    month = forms.ChoiceField(
        label="月",
        choices=settings.MONTH,
        widget=forms.Select(
            attrs={
                "class": "select-css is-size-7",
                "style": "width:10ch",
            }
        ),
        required=True,
    )

    accounting_class = forms.ModelChoiceField(
        label="会計区分",
        required=False,
        queryset=AccountingClass.objects.order_by("code"),
        empty_label="合算会計",
        widget=forms.Select(attrs={"class": "select-css is-size-7"}),
    )
