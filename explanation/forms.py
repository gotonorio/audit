from django import forms

from explanation.models import Description


class DescriptionCreateForm(forms.ModelForm):
    """データ入力説明文作成用フォーム"""

    class Meta:
        """https://docs.djangoproject.com/en/4.0/topics/forms/modelforms/#overriding-the-default-fields"""

        model = Description
        fields = ["no", "title", "description", "alive"]
        widgets = {
            "no": forms.NumberInput(
                attrs={
                    "class": "input",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "textarea",
                    "placeholder": " MarkDown記法が使えます",
                    "rows": "14",
                }
            ),
        }


class DescriptionListForm(forms.ModelForm):
    """説明書表示用Form"""

    class Meta:
        model = Description
        fields = [
            "title",
        ]

    title = forms.ModelChoiceField(
        queryset=Description.objects.filter(alive=True).order_by("no"),
        label="タイトル",
        empty_label="選択してください",
        error_messages={
            "required": "You didn't select a choice.",
            "invalid_choice": "invalid choice.",
        },
        required=False,
        initial="ALL",
        widget=forms.Select(attrs={"class": "select-css"}),
    )
