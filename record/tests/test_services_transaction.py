# record/tests/test_services_transaction.py
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from record.models import Account, Himoku, Transaction
from record.services.transaction import create_divided_transactions

User = get_user_model()


class CreateDividedTransactionsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.account = Account.objects.create(name="管理会計口座")
        self.himoku = Himoku.objects.create(
            code="999",
            himoku_name="不明",
            accounting_class_id=1,
        )

        self.base = Transaction.objects.create(
            account=self.account,
            transaction_date="2024-01-01",
            is_income=False,
            himoku=self.himoku,
            amount=10000,
            balance=0,
            author=self.user,
            is_manualinput=True,
            calc_flg=True,
        )

    def test_create_divided_transactions_success(self):
        divide_forms = [
            {"amount": 6000, "description": "A"},
            {"amount": 4000, "description": "B"},
        ]

        offset, divides = create_divided_transactions(
            base_transaction=self.base,
            divide_forms=divide_forms,
            user=self.user,
        )

        # --- 戻り値の検証 ---
        self.assertEqual(offset.amount, -10000)
        self.assertEqual(len(divides), 2)

        # --- DB件数 ---
        self.assertEqual(Transaction.objects.count(), 1 + 1 + 2)

        # --- 合計一致 ---
        total = sum(d.amount for d in divides)
        self.assertEqual(total, 10000)


class CreateDividedTransactionsRollbackTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test")
        self.account = Account.objects.create(name="口座")
        self.himoku = Himoku.objects.create(
            code="999",
            himoku_name="不明",
            accounting_class_id=1,
        )
        self.base = Transaction.objects.create(
            account=self.account,
            transaction_date="2024-01-01",
            is_income=False,
            himoku=self.himoku,
            amount=10000,
            balance=0,
            author=self.user,
            is_manualinput=True,
            calc_flg=True,
        )

    def test_rollback_when_error_occurs(self):
        divide_forms = [
            {"amount": 6000},
            {"amount": 5000},  # 合計不一致 → 例外
        ]

        with self.assertRaises(ValueError):
            create_divided_transactions(
                base_transaction=self.base,
                divide_forms=divide_forms,
                user=self.user,
            )

        # ❗ 追加されていないことを確認
        self.assertEqual(Transaction.objects.count(), 1)
