from django.urls import path

from .views import (
    balans_sheet_transform,
    billing_transform,
    cashflow_transform,
    claim_transform,
    inc_exp_transform,
    payment_approval_transform,
)

app_name = "kurasel_translator"
urlpatterns = [
    path("create_monthly/", inc_exp_transform.IncomeExpenseTransformView.as_view(), name="create_monthly"),
    path(
        "create_deposit/", cashflow_transform.DepositWithdrawalTransformView.as_view(), name="create_deposit"
    ),
    path(
        "create_payment/",
        payment_approval_transform.PaymentApprovalTransformView.as_view(),
        name="create_payment",
    ),
    path("create_bs/", balans_sheet_transform.BalanceSheetTransformView.as_view(), name="create_bs"),
    path("create_claim/", claim_transform.ClaimTransformView.as_view(), name="create_claim"),
    path("create_billing/", billing_transform.BillingTransformView.as_view(), name="create_billing"),
]
