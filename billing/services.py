# billing/services.py
from common.services import select_period

from .models import Billing


def get_billing_summary(year, month):
    """
    指定された年月の請求内訳、合計、表示用文字列を返す
    """
    # 期間の計算
    tstart, tend = select_period(year, month)

    # データの抽出とソート
    qs = Billing.get_billing_data_qs(tstart, tend).order_by("billing_item__code")

    # 合計金額の計算（モデルメソッドの呼び出し）
    total_billing = Billing.calc_total_billing(qs)

    # 表示用文字列の生成
    yyyymm = f"{year}年{month}月"

    return {
        "billing_list": qs,
        "total_billing": total_billing,
        "yyyymm": yyyymm,
    }
