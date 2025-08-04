from django.urls import path

# from check_record.views import inconsistency_check_views, kurasel_views
from check_record import views

app_name = "check_record"
urlpatterns = [
    # 支払い承認チェック
    path(
        "kurasel_ap_expense_check/",
        views.ApprovalExpenseCheckView.as_view(),
        name="kurasel_ap_expense_check",
    ),
    path(
        "kurasel_ap_expense_check/<int:year>/<str:month>/",
        views.ApprovalExpenseCheckView.as_view(),
        name="kurasel_ap_expense_check",
    ),
    # 月次支出報告チェック
    path(
        "kurasel_mr_expense_check/",
        views.MonthlyReportExpenseCheckView.as_view(),
        name="kurasel_mr_expense_check",
    ),
    path(
        "kurasel_mr_expense_check/<int:year>/<str:month>/",
        views.MonthlyReportExpenseCheckView.as_view(),
        name="kurasel_mr_expense_check",
    ),
    path(
        "expense_check/",
        views.IncosistencyCheckView.as_view(),
        name="expense_check",
    ),
    path(
        "expense_check/<int:year>/<str:month>/",
        views.IncosistencyCheckView.as_view(),
        name="expense_check",
    ),
    # 月次収入報告チェック
    path(
        "kurasel_mr_income_check/",
        views.MonthlyReportIncomeCheckView.as_view(),
        name="kurasel_mr_income_check",
    ),
    path(
        "kurasel_mr_income_check/<int:year>/<str:month>/",
        views.MonthlyReportIncomeCheckView.as_view(),
        name="kurasel_mr_income_check",
    ),
    # 請求金額内訳データチェック
    path(
        "kurasel_ba_income_check/",
        views.BillingAmountCheckView.as_view(),
        name="kurasel_billing_check",
    ),
    path(
        "kurasel_ba_income_check/<int:year>/<str:month>/",
        views.BillingAmountCheckView.as_view(),
        name="kurasel_billing_check",
    ),
    path(
        "year_income_check/",
        views.YearReportIncomeCheckView.as_view(),
        name="year_income_check",
    ),
    path(
        "year_income_check/<int:year>/",
        views.YearReportIncomeCheckView.as_view(),
        name="year_income_check",
    ),
    path(
        "year_expense_check/",
        views.YearReportExpenseCheckView.as_view(),
        name="year_expense_check",
    ),
    path(
        "year_expense_check/<int:year>/",
        views.YearReportExpenseCheckView.as_view(),
        name="year_expense_check",
    ),
]
