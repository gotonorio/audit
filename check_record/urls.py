from django.urls import path
from check_record.views import kurasel_views

app_name = "check_record"
urlpatterns = [
    # クラセル
    path(
        "kurasel_ap_expense_check/",
        kurasel_views.ApprovalExpenseCheckView.as_view(),
        name="kurasel_ap_expense_check",
    ),
    path(
        "kurasel_ap_expense_check/<int:year>/<str:month>/",
        kurasel_views.ApprovalExpenseCheckView.as_view(),
        name="kurasel_ap_expense_check",
    ),
    path(
        "kurasel_mr_expense_check/",
        kurasel_views.MonthlyReportExpenseCheckView.as_view(),
        name="kurasel_mr_expense_check",
    ),
    path(
        "kurasel_mr_expense_check/<int:year>/<str:month>/",
        kurasel_views.MonthlyReportExpenseCheckView.as_view(),
        name="kurasel_mr_expense_check",
    ),
    path(
        "kurasel_mr_income_check/",
        kurasel_views.MonthlyReportIncomeCheckView.as_view(),
        name="kurasel_mr_income_check",
    ),
    path(
        "kurasel_mr_income_check/<int:year>/<str:month>/",
        kurasel_views.MonthlyReportIncomeCheckView.as_view(),
        name="kurasel_mr_income_check",
    ),
]
