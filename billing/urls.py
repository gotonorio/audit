from django.urls import path

from billing import views

app_name = "billing"
urlpatterns = [
    # データ表示
    path("billing_list/", views.BillingListView.as_view(), name="billing_list"),
    path("billing_list/<int:year>/<int:month>/", views.BillingListView.as_view(), name="billing_list"),
]
