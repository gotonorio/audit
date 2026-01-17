# payment/mixins.py
from django.utils import timezone
from django.utils.timezone import localtime


class PaymentParamMixin:
    """支払い関係のGETパラメータを処理するMixin"""

    def get_payment_params(self):
        now = localtime(timezone.now())
        return {
            "year": int(self.request.GET.get("year") or now.year),
            "month": int(self.request.GET.get("month") or now.month),
            "day": int(self.request.GET.get("day") or 0),
            "list_order": int(self.request.GET.get("list_order") or 0),
        }
