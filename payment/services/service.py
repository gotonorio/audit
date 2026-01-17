# payment/services.py
import datetime

from common.services import select_period
from django.db.models import Sum

from payment.models import Payment


def get_payment_summary(year, month, day=0, list_order=0):
    """指定された期間の支払いデータと合計金額を取得"""
    tstart, tend = select_period(year, month)

    # 1. フィルタリング
    qs = Payment.objects.select_related("himoku")

    if day == 0:
        # 月間表示
        qs = qs.filter(payment_date__range=[tstart, tend])
    else:
        # 特定の日付表示
        payment_day = datetime.date(year, month, day)
        qs = qs.filter(payment_date=payment_day)

    # 2. 並び替え
    if list_order == 0:
        qs = qs.order_by("payment_date", "himoku__code")
    else:
        qs = qs.order_by("himoku__code", "payment_date")

    # 3. 合計計算（DB側で計算）
    total = qs.aggregate(total=Sum("payment"))["total"] or 0

    return qs, total
