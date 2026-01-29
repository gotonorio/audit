from django.urls import path

from monthly_report import views

from .views import balance_sheet_views, data_views, etcetera_views

app_name = "monthly_report"
urlpatterns = [
    # ------------------------------------------------------------------------
    # データ表示
    # ------------------------------------------------------------------------
    # 支出リスト
    path("expenslist/", views.MonthlyReportExpenseListView.as_view(), name="expenselist"),
    # 収入リスト
    path("incomelist/", views.MonthlyReportIncomeListView.as_view(), name="incomelist"),
    # 年間月別支出リスト
    path("year_expenselist/", views.YearExpenseListView.as_view(), name="year_expenselist"),
    # 年間月別収入リスト
    path("year_incomelist/", views.YearIncomeListView.as_view(), name="year_incomelist"),
    # 年間月別収支リスト
    path(
        "year_income_expenselist/", views.YearIncomeExpenseListView.as_view(), name="year_income_expenselist"
    ),
    path("unpaid_list/", views.etcetera_views.UnpaidBalanceListView.as_view(), name="unpaid_list"),
    # 長期修繕計画シミュレーション用データ
    path(
        "simulation_data_list/",
        views.etcetera_views.SimulationDataListView.as_view(),
        name="simulation_data_list",
    ),
    # 貸借対照表
    path("bs_table/", balance_sheet_views.BalanceSheetTableView.as_view(), name="bs_table"),
    path("bs_list/", balance_sheet_views.BalanceSheetListView.as_view(), name="bs_list"),
    # ------------------------------------------------------------------------
    # データ編集
    # ------------------------------------------------------------------------
    # create
    # path("create_income/", views.MonthlyReportIncomeCreateView.as_view(), name="create_income"),
    # path(
    #     "create_expense/",
    #     data_views.MonthlyReportExpenseCreateView.as_view(),
    #     name="create_expense",
    # ),
    path("create_bs/", data_views.BalanceSheetCreateView.as_view(), name="create_bs"),
    path(
        "create_bs_item/",
        data_views.BalanceSheetItemCreateView.as_view(),
        name="create_bs_item",
    ),
    # update
    path("update_income/<int:pk>/", views.MonthlyReportIncomeUpdateView.as_view(), name="update_income"),
    path(
        "update_expense/<int:pk>/",
        views.MonthlyReportExpenseUpdateView.as_view(),
        name="update_expense",
    ),
    path(
        "update_bs/<int:pk>",
        data_views.BalanceSheetUpdateView.as_view(),
        name="update_bs",
    ),
    path(
        "update_bs_item/<int:pk>",
        data_views.BalanceSheetItemUpdateView.as_view(),
        name="update_bs_item",
    ),
    # delete
    path("delete_income/<int:pk>/", views.DeleteIncomeView.as_view(), name="delete_income"),
    path(
        "delete_expense/<int:pk>/",
        views.DeleteExpenseView.as_view(),
        name="delete_expense",
    ),
    path(
        "delete_bs/<int:pk>",
        data_views.BalanceSheetDeleteView.as_view(),
        name="delete_bs",
    ),
    # check
    path(
        "chk_offset/",
        etcetera_views.CheckOffset.as_view(),
        name="chk_offset",
    ),
    path(
        "calcflg_check/",
        etcetera_views.CalcFlgCheckList.as_view(),
        name="calcflg_check",
    ),
]
