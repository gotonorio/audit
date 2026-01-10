from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime

User = get_user_model()


class BillingListViewTests(TestCase):
    """BillingListView の動作テスト"""

    def setUp(self):
        # 1. テストユーザーと権限の準備
        self.user = User.objects.create_user(username="testuser", password="password123")
        permission = Permission.objects.get(codename="view_transaction")
        self.user.user_permissions.add(permission)

        # 2. ログイン（self.client を使うことで Middleware を通るようにする）
        self.client.login(username="testuser", password="password123")
        self.url = reverse("billing:billing_list")

    def test_access_denied_returns_403(self):
        """raise_exception = True により、権限がない場合は403を返すことを確認"""
        self.client.logout()
        # 権限のないユーザーでログイン
        User.objects.create_user(username="no_perm", password="password")
        self.client.login(username="no_perm", password="password")

        response = self.client.get(self.url)
        # raise_exception = True なので 302(リダイレクト) ではなく 403
        self.assertEqual(response.status_code, 403)

    def test_context_data_with_get_params(self):
        """GETパラメータ ?year=2024&month=1 でアクセスした際のコンテキスト確認"""
        response = self.client.get(self.url, {"year": "2024", "month": "1"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["year"], "2024")
        self.assertEqual(response.context["month"], "1")
        self.assertEqual(response.context["yyyymm"], "2024年1月")

    def test_context_default_to_now(self):
        """引数なしの場合、現在の年月がデフォルトでセットされるか"""
        now = localtime(timezone.now())
        response = self.client.get(self.url)

        # デフォルト値（int）がViewでコンテキストに入る際の型を確認
        # View側で str(localtime(...).year) 等にしていない場合、型に注意
        self.assertEqual(int(response.context["year"]), now.year)
        self.assertEqual(int(response.context["month"]), now.month)
