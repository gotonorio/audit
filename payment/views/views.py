import logging

from common.mixins import PeriodParamMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse, reverse_lazy
from django.utils.http import urlencode
from django.views import generic
from payment.forms import (
    ApprovalPaymentCreateForm,
    ApprovalPaymentListForm,
    PaymentMethodCreateForm,
)
from payment.models import Payment, PaymentMethod
from payment.services.service import get_payment_summary

logger = logging.getLogger(__name__)


# payment/views.py


class PaymentAdminBase:
    """支払い管理の共通設定"""

    permission_required = "record.add_transaction"
    raise_exception = True
    success_url = reverse_lazy("payment:create_paymentmethod")


class PaymentListView(PermissionRequiredMixin, PeriodParamMixin, generic.TemplateView):
    """年月別の承認済み支払いの表示
    - PeriodParamMixinを継承してget_year_month_params()を呼び出す。
    """

    template_name = "payment/approval_payment_list.html"
    permission_required = ("record.view_transaction",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # common/mixins
        year, month = self.get_year_month_params()
        day = int(self.request.GET.get("day") or 0)
        list_order = int(self.request.GET.get("list_order") or 0)

        # Serviceからデータを取得
        qs, total = get_payment_summary(year, month, day, list_order)

        context.update(
            {
                "approval_list": qs,
                "total": total,
                "year": year,
                "month": month,
                "form": ApprovalPaymentListForm(
                    initial={
                        "year": year,
                        "month": month,
                        "day": day,
                        "list_order": list_order,
                    }
                ),
                # "form": ApprovalPaymentListForm(initial=p),
            }
        )
        return context


class UpdatePaymentView(PaymentAdminBase, PermissionRequiredMixin, generic.UpdateView):
    """支払い承認データの修正"""

    model = Payment
    form_class = ApprovalPaymentCreateForm
    template_name = "payment/update_form.html"

    def get_success_url(self):
        # 保存後、元の年月のリスト画面に戻す
        base_url = reverse("payment:payment_list")
        params = urlencode(
            {
                "year": self.object.payment_date.year,
                "month": self.object.payment_date.month,
            }
        )
        return f"{base_url}?{params}"


class PaymentMethodBase(PaymentAdminBase):
    """支払い方法設定画面の共通ロジック（一覧表示を同梱）"""

    model = PaymentMethod
    form_class = PaymentMethodCreateForm
    template_name = "payment/payment_method_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = PaymentMethod.objects.all()
        return context


class PaymentMethodCreateView(PaymentMethodBase, PermissionRequiredMixin, generic.CreateView):
    """支払い方法の作成"""

    pass


class PaymentMethodUpdateView(PaymentMethodBase, PermissionRequiredMixin, generic.UpdateView):
    """支払い方法の更新"""

    pass


# class PaymentListView(PermissionRequiredMixin, generic.TemplateView):
#     """年月別の承認済み支払いの表示"""

#     model = Payment
#     template_name = "payment/approval_payment_list.html"
#     permission_required = ("record.view_transaction",)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # GETパラメータ(self.request.GET)
#         # .get() で None が返ることを利用して 'or' で繋ぐ
#         now = localtime(timezone.now())
#         year = self.request.GET.get("year") or now.year
#         month = self.request.GET.get("month") or now.month
#         day = self.request.GET.get("day") or "0"
#         list_order = self.request.GET.get("list_order") or "0"

#         year = int(year)
#         month = int(month)
#         day = int(day)
#         list_order = int(list_order)

#         # querysetの作成。
#         tstart, tend = select_period(year, month)
#         if day == 0:
#             qs = Payment.objects.select_related("himoku").filter(payment_date__range=[tstart, tend])
#         elif month == 0:
#             qs = (
#                 Payment.objects.select_related("himoku")
#                 .filter(payment_date__range=[tstart, tend])
#                 .filter(payment_date__day=day)
#             )
#         else:
#             payment_day = datetime.datetime(year, month, day)
#             qs = Payment.objects.all().select_related("himoku").filter(payment_date=payment_day)
#         # 表示順序
#         if list_order == 0:
#             qs = qs.order_by("payment_date", "himoku__code")
#         else:
#             qs = qs.order_by("himoku__code", "payment_date")
#         # 支払い金額の合計
#         total = 0
#         for data in qs:
#             total += data.payment
#         # forms.pyのKeikakuListFormに初期値を設定する
#         form = ApprovalPaymentListForm(
#             initial={
#                 "year": year,
#                 "month": month,
#                 "day": day,
#                 "list_order": list_order,
#             }
#         )
#         context["approval_list"] = qs
#         context["form"] = form
#         context["total"] = total
#         context["year"] = year
#         context["month"] = month
#         return context


# class UpdatePaymentView(PermissionRequiredMixin, generic.UpdateView):
#     """支払い承認データ（作成はKuraselからの取り込みなので、修正処理だけが必要）"""

#     model = Payment
#     form_class = ApprovalPaymentCreateForm
#     template_name = "payment/update_form.html"
#     permission_required = "record.add_transaction"
#     # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
#     raise_exception = True

#     def get_success_url(self):
#         """保存成功後、GETパラメータを付与した一覧画面へリダイレクト"""
#         base_url = reverse("payment:payment_list")

#         # クエリパラメータを辞書形式で定義
#         params = urlencode(
#             {
#                 "year": self.object.payment_date.year,
#                 "month": self.object.payment_date.month,
#             }
#         )
#         return f"{base_url}?{params}"


# class PaymentMethodCreateView(PermissionRequiredMixin, generic.CreateView):
#     """支払い方法の作成処理
#     支払い方法の一覧表示も同じ画面で行う。
#     """

#     model = PaymentMethod
#     form_class = PaymentMethodCreateForm
#     template_name = "payment/payment_method_form.html"
#     permission_required = "record.add_transaction"
#     # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
#     raise_exception = True
#     # 保存が成功した場合に遷移するurl
#     success_url = reverse_lazy("payment:create_paymentmethod")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["object_list"] = PaymentMethod.objects.all()
#         return context


# class PaymentMethodUpdateView(PermissionRequiredMixin, generic.UpdateView):
#     """支払い方法データの UpdateView"""

#     model = PaymentMethod
#     form_class = PaymentMethodCreateForm
#     template_name = "payment/payment_method_form.html"
#     permission_required = "record.add_transaction"
#     # 権限がない場合、Forbidden 403を返す。これがない場合はログイン画面に飛ばす。
#     raise_exception = True
#     # 保存が成功した場合に遷移するurl
#     success_url = reverse_lazy("payment:create_paymentmethod")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["object_list"] = PaymentMethod.objects.all()
#         return context
