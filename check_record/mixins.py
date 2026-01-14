# check_record/mixins.py
from django.utils import timezone
from django.utils.timezone import localtime


class IncomeCheckParamMixin:
    def get_params(self):
        now = localtime(timezone.now())
        year = int(self.request.GET.get("year") or now.year)
        month = int(self.request.GET.get("month") or now.month)
        return year, month
