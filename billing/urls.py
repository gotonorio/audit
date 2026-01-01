from django.urls import path

from billing import views

app_name = "billing"
urlpatterns = [
    # 請求合計金額内訳リスト
    path("billing_list/", views.BillingListView.as_view(), name="billing_list"),
]
