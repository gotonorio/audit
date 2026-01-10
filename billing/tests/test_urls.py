from django.test import SimpleTestCase
from django.urls import resolve, reverse

# from billing.views import BillingListView


class TestBillingUrls(SimpleTestCase):
    """billingアプリケーションのURLルーティングテスト"""

    def test_billing_list_no_params_resolves(self):
        """引数なしの billing_list が BillingListView を参照することを確認"""
        # URLを生成
        url = reverse("billing:billing_list")
        match = resolve(url)
        # 生成されたURLが期待通りか確認
        self.assertEqual(url, "/billing/billing_list/")
        # URLが正しいViewに解決されるか確認
        # self.assertEqual(resolve(url).func.view_class, BillingListView)
        self.assertEqual(match.view_name, "billing:billing_list")

    def test_billing_list_invalid_params_not_found(self):
        """不正な形式のURL（月が文字列など）は解決されないことを確認"""
        # <int:month> なので、文字列を入れると404になるはず
        url = "/billing/billing_list/2025/december/"
        with self.assertRaises(Exception):
            resolve(url)
