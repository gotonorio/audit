from django.urls import path

from .views import data_views, views

app_name = "monthly_report"
urlpatterns = [
    # ------------------------------------------------------------------------
    # データ表示
    # ------------------------------------------------------------------------
    path("expenslist/", views.MonthlyReportExpenseListView.as_view(), name="expenselist"),
    path("incomelist/", views.MonthlyReportIncomeListView.as_view(), name="incomelist"),
    path(
        "year_expenselist/",
        views.YearExpenseListView.as_view(),
        name="year_expenselist",
    ),
    path(
        "year_incomelist/",
        views.YearIncomeListView.as_view(),
        name="year_incomelist",
    ),
    path("bs_table/", views.BalanceSheetTableView.as_view(), name="bs_table"),
    path(
        "bs_table/<int:year>/<int:month>/<int:ac_class>/",
        views.BalanceSheetTableView.as_view(),
        name="bs_table",
    ),
    path("bs_list/", views.BalanceSheetListView.as_view(), name="bs_list"),
    path(
        "bs_list/<int:year>/<int:month>/<int:ac_class>/",
        views.BalanceSheetListView.as_view(),
        name="bs_list",
    ),
    # update後に元の画面に戻る処理
    path(
        "expenslist/<int:year>/<int:month>/<int:ac_class>/",
        views.MonthlyReportExpenseListView.as_view(),
        name="expenselist",
    ),
    path(
        "incomelist/<int:year>/<int:month>/<int:ac_class>/",
        views.MonthlyReportIncomeListView.as_view(),
        name="incomelist",
    ),
    path(
        "year_expenselist/<int:year>/<int:ac_class>/",
        views.YearExpenseListView.as_view(),
        name="year_expenselist",
    ),
    path(
        "year_incomelist/<int:year>/<int:ac_class>/",
        views.YearIncomeListView.as_view(),
        name="year_incomelist",
    ),
    # ------------------------------------------------------------------------
    # データ編集
    # ------------------------------------------------------------------------
    path(
        "create_income/",
        data_views.MonthlyReportIncomeCreateView.as_view(),
        name="create_income",
    ),
    path(
        "update_income/<int:pk>/",
        data_views.MonthlyReportIncomeUpdateView.as_view(),
        name="update_income",
    ),
    path(
        "create_expense/",
        data_views.MonthlyReportExpenseCreateView.as_view(),
        name="create_expense",
    ),
    path(
        "update_expense/<int:pk>/",
        data_views.MonthlyReportExpenseUpdateView.as_view(),
        name="update_expense",
    ),
    path(
        "delete_income/<int:pk>/",
        data_views.DeleteIncomeView.as_view(),
        name="delete_income",
    ),
    path(
        "delete_expense/<int:pk>/",
        data_views.DeleteExpenseView.as_view(),
        name="delete_expense",
    ),
    path("create_bs/", data_views.BalanceSheetCreateView.as_view(), name="create_bs"),
    path(
        "update_bs/<int:pk>",
        data_views.BalanceSheetUpdateView.as_view(),
        name="update_bs",
    ),
    path(
        "delete_bs/<int:pk>",
        data_views.BalanceSheetDeleteView.as_view(),
        name="delete_bs",
    ),
    path(
        "create_bs_item/",
        data_views.BalanceSheetItemCreateView.as_view(),
        name="create_bs_item",
    ),
    path(
        "update_bs_item/<int:pk>",
        data_views.BalanceSheetItemUpdateView.as_view(),
        name="update_bs_item",
    ),
    path(
        "chk_offset/",
        views.CheckOffset.as_view(),
        name="chk_offset",
    ),
]
