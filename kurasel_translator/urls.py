from django.urls import path

from .views import balance_sheet, billing, deposit_withdraw, monthly_balance, views

app_name = "kurasel_translator"
urlpatterns = [
    path("create_monthly/", monthly_balance.MonthlyBalanceView.as_view(), name="create_monthly"),
    path(
        "create_monthly/<int:year>/<str:month>/",
        monthly_balance.MonthlyBalanceView.as_view(),
        name="create_monthly",
    ),
    path("create_deposit/", deposit_withdraw.DepositWithdrawalView.as_view(), name="create_deposit"),
    path("create_payment/", views.PaymentAuditView.as_view(), name="create_payment"),
    path("create_bs/", balance_sheet.BalanceSheetTranslateView.as_view(), name="create_bs"),
    path("create_claim/", views.ClaimTranslateView.as_view(), name="create_claim"),
    path("create_billing/", billing.BillingIntakeView.as_view(), name="create_billing"),
]
