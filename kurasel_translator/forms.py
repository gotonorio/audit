from django import forms
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import localtime  # view.pyでローカルタイムのため追加
from passbook.forms import YearMonthForm
from record.models import AccountingClass

KIND = (
    ("収入", "収入"),
    ("支出", "支出"),
)


class DepositWithdrawalForm(forms.Form):
    """入出金明細入力フォーム"""

    year = forms.IntegerField(
        label="西暦",
        widget=forms.NumberInput(attrs={"class": "input"}),
        initial=localtime(timezone.now()).year,
    )
    mode = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "select-css"}),
        label="モード",
        choices=(
            ("確認", "確認"),
            ("登録", "登録"),
        ),
    )
    note = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "placeholder": "ヘッダー部を除いてコピーしてください。",
                "class": "textarea",
                "rows": 10,
            }
        ),
        label="内容",
    )


class MonthlyBalanceForm(DepositWithdrawalForm):
    """月次収支入力フォーム
    - DepositWithdrawalFormを継承する。
    - Kuraselでは管理会計、修繕会計に同じ「受取利息」費目があるため、
    管理会計では「受取利息」を「雑収入」として記録するため、会計区分フラグを使う。
    （口座は一つなのに...）
    """

    # month = forms.IntegerField(
    #     label="月",
    #     initial=localtime(timezone.now()).month,
    #     widget=forms.NumberInput(attrs={"class": "input"}),
    # )
    month = forms.ChoiceField(
        label="月",
        initial=localtime(timezone.now()).month,
        widget=forms.Select(attrs={"class": "select-css"}),
        choices=settings.MONTH,
    )
    kind = forms.ChoiceField(
        label="収支区分",
        widget=forms.Select(attrs={"class": "select-css"}),
        choices=(
            ("収入", "収入"),
            ("支出", "支出"),
        ),
    )
    accounting_class = forms.ModelChoiceField(
        label="会計区分",
        required=True,
        queryset=AccountingClass.objects.all().order_by("code"),
        initial=0,
        widget=forms.Select(attrs={"class": "select-css"}),
    )


class PaymentAuditForm(DepositWithdrawalForm):
    """Kuraselの承認された支払管理データを読み込むためのForm"""

    month = forms.ChoiceField(
        label="月",
        initial=localtime(timezone.now()).month,
        widget=forms.Select(attrs={"class": "select-css"}),
        choices=settings.MONTH,
    )
    # month = forms.IntegerField(
    #     label="月",
    #     initial=localtime(timezone.now()).month,
    #     widget=forms.NumberInput(attrs={"class": "input"}),
    # )
    day = forms.ChoiceField(
        label="支払日",
        widget=forms.Select(attrs={"class": "select-css"}),
        choices=(
            ("25", "25日払い"),
            ("10", "10日払い"),
        ),
    )


class BalanceSheetTranslateForm(DepositWithdrawalForm):
    """貸借対照表入力フォーム
    - DepositWithdrawalFormを継承する。
    - Kuraselでは管理会計、修繕会計に同じ「受取利息」費目があるため、
    管理会計では「受取利息」を「雑収入」として記録するため、会計区分フラグを使う。
    （口座は一つなのに...）
    """

    # month = forms.IntegerField(
    #     label="月",
    #     initial=localtime(timezone.now()).month,
    #     widget=forms.NumberInput(attrs={"class": "input"}),
    # )
    month = forms.ChoiceField(
        label="月",
        initial=localtime(timezone.now()).month,
        widget=forms.Select(attrs={"class": "select-css"}),
        choices=settings.MONTH,
    )
    accounting_class = forms.ModelChoiceField(
        label="会計区分",
        required=True,
        queryset=AccountingClass.objects.all().order_by("code"),
        initial=0,
        widget=forms.Select(attrs={"class": "select-css"}),
    )


class ClaimTranslateForm(DepositWithdrawalForm):
    """貸借対照表入力フォーム
    - DepositWithdrawalFormを継承する。
    - Kuraselでは管理会計、修繕会計に同じ「受取利息」費目があるため、
    管理会計では「受取利息」を「雑収入」として記録するため、会計区分フラグを使う。
    （口座は一つなのに...）
    """

    month = forms.ChoiceField(
        label="月",
        initial=localtime(timezone.now()).month,
        widget=forms.Select(attrs={"class": "select-css"}),
        choices=settings.MONTH,
    )
    claim_type = forms.ChoiceField(
        label="請求種別",
        choices=settings.CLAIMTYPE,
        initial="滞納金",
        widget=forms.Select(attrs={"class": "select-css"}),
    )
