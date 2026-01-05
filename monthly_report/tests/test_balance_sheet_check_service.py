from django.test import TestCase
from django.utils import timezone
from monthly_report.models import BalanceSheet, BalanceSheetItem, ReportTransaction
from monthly_report.services.balance_sheet_check_service import check_balancesheet
from record.models import AccountingClass


class BalanceSheetCheckServiceTests(TestCase):
    """check_balancesheet の単体テスト"""

    def setUp(self):
        self.ac = AccountingClass.objects.create(
            code=1,
            accounting_name="一般会計",
        )

        self.bank_item = BalanceSheetItem.objects.create(
            code=1,
            item_name="銀行残高",
            is_asset=True,
            ac_class=self.ac,
        )

        # 前月
        BalanceSheet.objects.create(
            monthly_date=timezone.datetime(2024, 12, 31).date(),
            item_name=self.bank_item,
            amounts=100_000,
        )

        # 当月
        BalanceSheet.objects.create(
            monthly_date=timezone.datetime(2025, 1, 31).date(),
            item_name=self.bank_item,
            amounts=120_000,
        )

        ReportTransaction.objects.create(
            transaction_date=timezone.datetime(2025, 1, 15).date(),
            amount=20_000,
            himoku=None,
            calc_flg=True,
            accounting_class=self.ac,
        )

    def test_check_balancesheet_success(self):
        prev, curr = check_balancesheet(2025, 1, self.ac.id)

        self.assertIsNotNone(prev)
        self.assertIsNotNone(curr)

        self.assertIn("計算現金残高", curr)
