from django.urls import path
from . import views

app_name = "kurasel_translator"
urlpatterns = [
    path("create/", views.MonthlyBalanceView.as_view(), name="create"),
    path(
        "create_deposit/", views.DepositWithdrawalView.as_view(), name="create_deposit"
    ),
    path("create_payment/", views.PaymentAuditView.as_view(), name="create_payment"),
    path("create_bs/", views.BalanceSheetTranslateView.as_view(), name="create_bs"),
]
