import logging

from django import forms
from django.conf import settings
from django.utils import timezone
from passbook.forms import YearMonthForm

from record.models import (
    Account,
    AccountingClass,
    ApprovalCheckData,
    ClaimData,
    Himoku,
    Transaction,
    TransferRequester,
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# データ表示用Form
# -----------------------------------------------------------------------------
class TransactionDisplayForm(YearMonthForm):
    """通帳取引明細表示用Form"""

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
        choices=[(0, "ALL")] + settings.MONTH,
        required=True,
    )
    # 会計区分
    ac_class = forms.ModelChoiceField(
        label="会計区分",
        required=False,
        queryset=AccountingClass.objects.order_by("code"),
        empty_label="会計区分ALL",
        widget=forms.Select(attrs={"class": "select-css is-size-7"}),
    )
    # 費目順表示順序
    list_order = forms.ChoiceField(
        label="費目順",
        widget=forms.Select(attrs={"class": "select-css is-size-7"}),
        choices=(
            (0, "日付順"),
            (1, "費目順"),
        ),
        required=True,
    )
    # 費目
    himoku_id = forms.ModelChoiceField(
        label="入出金費目",
        empty_label="全費目",
        required=False,
        queryset=Himoku.objects.filter(alive=True, code__lt=9000).order_by(
            "-is_income", "accounting_class", "code"
        ),
        widget=forms.Select(attrs={"class": "select-css is-size-7"}),
    )


# -----------------------------------------------------------------------------
# データ登録用Form
# -----------------------------------------------------------------------------
class TransactionCreateForm(forms.ModelForm):
    """入出金明細データ登録・編集用フォーム"""

    account = forms.ModelChoiceField(
        label="口座名",
        required=True,
        queryset=Account.objects.filter(alive=True),
        widget=forms.Select(attrs={"class": "select-css"}),
    )

    himoku = forms.ModelChoiceField(
        label="費目選択",
        required=False,
        queryset=Himoku.objects.filter(alive=True, code__lt=9000).order_by(
            "-is_income", "accounting_class", "code"
        ),
        widget=forms.Select(attrs={"class": "select-css"}),
    )
    # requiredをFalseにするため上書きする。
    requesters_name = forms.CharField(
        label="振込依頼人名",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "input",
            }
        ),
    )
    description = forms.CharField(
        label="摘要",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "textarea",
                "rows": 3,
            }
        ),
    )

    class Meta:
        model = Transaction
        fields = [
            "account",
            "transaction_date",
            "amount",
            "himoku",
            "requesters_name",
            "description",
            "is_income",
            "calc_flg",
            "is_maeukekin",
            # "is_mishuukin",
            "is_approval",
            "is_manualinput",
            "is_billing",
            "is_miharai",
        ]
        labels = {"calc_flg": "チェック計算対象(calc_flg)", "is_manualinput": "手動入力Flg"}
        widgets = {
            "transaction_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "is-size-6",
                }
            ),
        }
        help_texts = {
            "is_manualinput": "※ 相殺、前受金等の補正データではチェックする。",
            "is_income": "※ 入金の場合はチェックする。",
            "calc_flg": "※ 資金移動の場合はチェックしない。",
            "is_approval": "※ 収入項目、支払い承認が不要の場合はチェックを外す。",
            "is_billing": "※ 請求金額合計内訳の項目の場合はチェックする。",
            "is_maeukekin": "※ 請求承認期日後に振込みされた入金は前受金となるのでチェックする。",
            # "is_mishuukin": "※ 未収金の振込の場合はチェックする。",
            "is_miharai": "※ 前期の未払い分の支出ではチェックする",
        }

    def clean_transaction_date(self):
        """未来の日付をチェック"""
        td = self.cleaned_data.get("transaction_date")
        # awareなdatetime.dateをnaiveなdatetime.datetimeに変更して比較する。
        transaction_date = timezone.datetime(td.year, td.month, td.day, 0, 0, 0)
        today = timezone.datetime.today()
        if transaction_date > today:
            raise forms.ValidationError("未来の日付です！")
        return td


class HimokuForm(forms.ModelForm):
    """費目マスタデータ登録/修正用Form"""

    accounting_class = forms.ModelChoiceField(
        label="会計区分",
        queryset=AccountingClass.objects.all().order_by("code"),
        widget=forms.Select(attrs={"class": "select-css"}),
    )

    class Meta:
        model = Himoku
        fields = [
            "code",
            "himoku_name",
            "accounting_class",
            "is_income",
            "alive",
            "aggregate_flag",
            "is_approval",
            "is_default",
            "is_community",
            "is_unbilled_income",
            "comment",
        ]
        labels = {"aggregate_flag": "集計:(aggregate_flag)"}
        widgets = {
            "code": forms.NumberInput(
                attrs={
                    "class": "input",
                }
            ),
            "himoku_name": forms.TextInput(
                attrs={
                    "class": "input",
                    # 'readonly': 'readonly',
                }
            ),
            "comment": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
        }
        help_texts = {
            "code": "* 有効だが非表示にする費目は、費目コードを9000以上に設定する。",
            "himoku_name": "* 費目名はKuraselの費目名に合わせる。",
            "alive": "* 必要のない費目は削除ではなく、有効フラグのチェックを外す。",
            "aggregate_flag": "* クラセル監査の集計計算に含めるかのフラグ。基本的にチェックする<br>（同一口座内の会計区分間の資金移動、共用保険料の支出、町会費の支出はチェックを外す）",
            "is_approval": "* 入出金明細データで承認が必要な費目。<br>（電気・水道料金の口座振替、管理業務委託費などはチェックを外す）",
            "is_default": "* 入出金明細データの取込みで、デフォルトで設定される費目名にチェックする。<br>（「不明」という費目をデフォルトとする）",
            "is_community": "* 町内会支出の場合にチェックする。",
            "is_unbilled_income": "* 未請求入金の場合にチェックする。",
        }


class AccountTitleForm(forms.ModelForm):
    """科目データ"""

    class Meta:
        widgets = {
            "code": forms.NumberInput(
                attrs={
                    "class": "input",
                }
            ),
            "account_title_name": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
        }


class RequesterForm(forms.ModelForm):
    """振込依頼者データ登録/修正用Form"""

    himoku = forms.ModelChoiceField(
        label="費目選択",
        required=False,
        queryset=Himoku.objects.filter(alive=True, is_income=False, code__lt=9000).order_by(
            "-is_income", "code"
        ),
        widget=forms.Select(attrs={"class": "select-css"}),
    )

    class Meta:
        model = TransferRequester
        fields = [
            "requester",
            "himoku",
            "comment",
        ]
        widgets = {
            "requester": forms.TextInput(
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


class TransactionOffsetForm(TransactionCreateForm):
    """取引明細データの相殺処理用Form
    - 不要なformフィールドは表示しない。
    - forms.HiddenInput()を使うため、TransactionCreateFormを継承。
    """

    class Meta(TransactionCreateForm.Meta):
        widgets = {
            # form画面で非表示にする。
            "is_income": forms.HiddenInput(),
            "balance": forms.HiddenInput(),
            "is_manualinput": forms.HiddenInput(),
            "calc_flg": forms.HiddenInput(),
        }


class TransactionDivideForm(forms.Form):
    """相殺処理されたデータの分割データ入力form"""

    # 金額
    amount = forms.IntegerField(
        label="金額",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "input right-aligned-input",
            }
        ),
    )
    # 振込依頼人
    requesters_name = forms.CharField(
        label="振込依頼人",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "input",
            }
        ),
    )
    # 摘要
    description = forms.CharField(
        label="摘要",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "input",
            }
        ),
    )


# TransactionDivideFormを複数（settings.FORMSET_NUM）並べるためのFormSet。
TransactionDivideFormSet = forms.formset_factory(TransactionDivideForm, extra=settings.FORMSET_NUM)


class HimokuCsvFileSelectForm(forms.Form):
    """CSVファイル選択用フォーム
    https://docs.djangoproject.com/ja/2.0/topics/http/file-uploads/#top
    https://docs.djangoproject.com/ja/2.2/ref/forms/validation/
    """

    file = forms.FileField(label="CSVファイル", help_text="**")

    def clean_file(self):
        file = self.cleaned_data["file"]
        if file.name.endswith(".csv"):
            return file
        else:
            raise forms.ValidationError("拡張子がcsvのファイルをアップロードしてください")

    # fieldにcssを設定するためのclassを設定する。
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].widget.attrs["class"] = "filefield is-size-7"


class HimokuListForm(forms.Form):
    """費目アップデート用リスト表示"""

    accounting_class = forms.ModelChoiceField(
        label="会計区分",
        queryset=AccountingClass.objects.all().order_by("code"),
        empty_label="会計区分ALL",
        required=False,
        widget=forms.Select(attrs={"class": "select-css"}),
    )


class ApprovalCheckDataForm(forms.ModelForm):
    """振込依頼者データ登録/修正用Form"""

    atext = forms.CharField(
        label="摘要欄の判定文字列",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "input",
            }
        ),
    )

    class Meta:
        model = ApprovalCheckData
        fields = [
            "atext",
            "comment",
            "alive",
        ]
        widgets = {
            "atext": forms.TextInput(
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


class RecalcBalanceForm(forms.Form):
    """通帳残高チェック用"""

    sdate = forms.DateField(
        label="残高基準日",
        required=True,
        help_text="* 残高の判明している基準日を設定。",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "is-size-6",
            }
        ),
    )
    balance = forms.IntegerField(
        label="基準日残高",
        required=True,
        help_text="* 基準日の最終残高を設定。",
        widget=forms.NumberInput(attrs={"class": "input"}),
    )


class ClaimListForm(forms.Form):
    """管理費等請求データ一覧表示用Form"""

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
        choices=[(0, "ALL")] + settings.MONTH,
        required=True,
    )
    # データ区分
    claim_type = forms.ChoiceField(
        label="会計区分",
        required=False,
        choices=settings.CLAIMTYPE,
        widget=forms.Select(attrs={"class": "select-css is-size-7"}),
    )


class ClaimUpdateForm(forms.ModelForm):
    """振込依頼者データ登録/修正用Form"""

    comment = forms.CharField(
        label="摘要",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "input",
            }
        ),
    )

    class Meta:
        model = ClaimData
        fields = [
            "claim_date",
            "claim_type",
            "room_no",
            "name",
            "comment",
        ]
        widgets = {
            "comment": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
        }

    # fieldにcssを設定するためのclassを設定する。
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["claim_date"].disabled = True
        self.fields["claim_type"].disabled = True
        self.fields["room_no"].disabled = True
        self.fields["name"].disabled = True
