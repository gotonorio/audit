from django.test import TestCase
from django.utils import timezone
from monthly_report.models import BalanceSheet, BalanceSheetItem
from monthly_report.services.balance_sheet_service import (
    fetch_balancesheet_by_class,
    make_balancesheet,
)
from record.models import AccountingClass


class BalanceSheetServiceTests(TestCase):
    """balance_sheet_service の単体テスト"""

    def setUp(self):
        self.ac = AccountingClass.objects.create(
            code=1,
            accounting_name="一般会計",
        )

        self.asset_item = BalanceSheetItem.objects.create(
            code=1,
            item_name="銀行残高",
            is_asset=True,
            ac_class=self.ac,
        )

        self.debt_item = BalanceSheetItem.objects.create(
            code=2,
            item_name="未払金",
            is_asset=False,
            ac_class=self.ac,
        )

        self.date = timezone.datetime(2025, 1, 31).date()

        BalanceSheet.objects.create(
            monthly_date=self.date,
            item_name=self.asset_item,
            amounts=100_000,
        )

        BalanceSheet.objects.create(
            monthly_date=self.date,
            item_name=self.debt_item,
            amounts=30_000,
        )

    # ------------------------------------------------------------------
    # fetch_balancesheet_by_class
    # ------------------------------------------------------------------
    def test_fetch_balancesheet_by_class(self):
        tstart = timezone.datetime(2025, 1, 1).date()
        tend = timezone.datetime(2025, 1, 31).date()

        asset, debt = fetch_balancesheet_by_class(tstart, tend, self.ac.id)

        self.assertEqual(len(asset), 1)
        self.assertEqual(len(debt), 1)

        self.assertEqual(asset[0][0], "銀行残高")
        self.assertEqual(asset[0][1], 100_000)

        self.assertEqual(debt[0][0], "未払金")
        self.assertEqual(debt[0][1], 30_000)

    # ------------------------------------------------------------------
    # make_balancesheet
    # ------------------------------------------------------------------
    def test_make_balancesheet(self):
        asset = [["銀行残高", 100_000, None]]
        debt = [["未払金", 30_000, None]]

        asset, debt, total = make_balancesheet(asset, debt)

        self.assertEqual(total, 100_000)

        # 負債合計
        self.assertIn(["負債の部合計", 30_000, None], debt)

        # 剰余金
        self.assertIn(["剰余の部合計", 70_000, None], debt)
