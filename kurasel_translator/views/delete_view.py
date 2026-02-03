from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import urlencode
from django.views.generic import FormView
from payment.forms import MonthYearSelectionForm


class PaymentDeleteByYearMonthView(PermissionRequiredMixin, FormView):
    """指定された年月の支払いデータを一括削除するFormView"""

    template_name = "payment/payment_delete_by_yearmonth.html"
    form_class = MonthYearSelectionForm
    success_url = reverse_lazy("payment:payment_list")  # 削除後にリダイレクトする先

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            year = form.cleaned_data["year"]
            month = form.cleaned_data["month"]

            # 「実行ボタン」が押された場合のみ削除
            if "execute_delete" in request.POST:
                count = Payment.delete_by_yearmonth(year, month)
                messages.success(request, f"{year}年{month}月のデータを {count} 件削除しました。")
                return redirect(self.get_success_url())

            # 「確認ボタン」が押された場合は、データを抽出して同じページを表示
            target_data = Payment.objects.filter(payment_date__year=year, payment_date__month=month)
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    target_data=target_data,
                    confirm_mode=True,  # 確認モードフラグ
                    year=year,
                    month=month,
                )
            )
        return self.form_invalid(form)
