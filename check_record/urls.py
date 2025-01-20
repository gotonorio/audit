from django.urls import path

from check_record.views import inconsistency_check_views, kurasel_views

app_name = "check_record"
urlpatterns = [
    # 支払い承認チェック
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
    # 月次支出報告チェック
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
        "expense_check/",
        inconsistency_check_views.IncosistencyCheckView.as_view(),
        name="expense_check",
    ),
    path(
        "expense_check/<int:year>/<str:month>/",
        inconsistency_check_views.IncosistencyCheckView.as_view(),
        name="expense_check",
    ),
    # 月次収入報告チェック
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
    # 請求金額内訳データチェック
    path(
        "kurasel_ba_income_check/",
        kurasel_views.BillingAmountCheckView.as_view(),
        name="kurasel_billing_check",
    ),
    path(
        "kurasel_ba_income_check/<int:year>/<str:month>/",
        kurasel_views.BillingAmountCheckView.as_view(),
        name="kurasel_billing_check",
    ),
    path(
        "year_income_check/",
        kurasel_views.YearReportIncomeCheckView.as_view(),
        name="year_income_check",
    ),
    path(
        "year_income_check/<int:year>/",
        kurasel_views.YearReportIncomeCheckView.as_view(),
        name="year_income_check",
    ),
    path(
        "year_expense_check/",
        kurasel_views.YearReportExpenseCheckView.as_view(),
        name="year_expense_check",
    ),
    path(
        "year_expense_check/<int:year>/",
        kurasel_views.YearReportExpenseCheckView.as_view(),
        name="year_expense_check",
    ),
]
