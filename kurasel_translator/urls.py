from django.urls import path

from .views import (
    balans_sheet_transform,
    billing_transform,
    claim_transform,
    monthly_report_transform,
    payment_approval_transform,
    transaction_transform,
)

app_name = "kurasel_translator"
urlpatterns = [
    path(
        "create_monthly/", monthly_report_transform.MonthlyReportImportView.as_view(), name="create_monthly"
    ),
    path("create_deposit/", transaction_transform.TransactionImportView.as_view(), name="create_deposit"),
    path(
        "create_payment/",
        payment_approval_transform.PaymentApprovalTransformView.as_view(),
        name="create_payment",
    ),
    path("create_bs/", balans_sheet_transform.BalanceSheetTransformView.as_view(), name="create_bs"),
    path("create_claim/", claim_transform.ClaimTransformView.as_view(), name="create_claim"),
    path("create_billing/", billing_transform.BillingTransformView.as_view(), name="create_billing"),
]
