# common/mixins.py
from django.utils import timezone
from django.utils.timezone import localtime


class PeriodParamMixin:
    """年月のパラメータ取得を共通化"""

    def get_year_month_params(self):
        now = localtime(timezone.now())
        year = int(self.request.GET.get("year") or now.year)
        month = int(self.request.GET.get("month") or now.month)
        return year, month
