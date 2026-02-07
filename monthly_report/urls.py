from django.urls import path

from monthly_report import views

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
        "year_income_expenselist/",
        views.YearIncomeExpenseListView.as_view(),
        name="year_income_expenselist",
    ),
    path("unpaid_list/", views.UnpaidBalanceListView.as_view(), name="unpaid_list"),
    # 長期修繕計画シミュレーション用データ
    path(
        "simulation_data_list/",
        views.SimulationDataListView.as_view(),
        name="simulation_data_list",
    ),
    # 貸借対照表
    path("bs_table/", views.BalanceSheetTableView.as_view(), name="bs_table"),
    path("bs_list/", views.BalanceSheetListView.as_view(), name="bs_list"),
    # ------------------------------------------------------------------------
    # データ編集
    # ------------------------------------------------------------------------
    path("create_bs/", views.BalanceSheetCreateView.as_view(), name="create_bs"),
    path(
        "create_bs_item/",
        views.BalanceSheetItemCreateView.as_view(),
        name="create_bs_item",
    ),
    # update
    path(
        "update_income/<int:pk>/",
        views.MonthlyReportIncomeUpdateView.as_view(),
        name="update_income",
    ),
    path(
        "update_expense/<int:pk>/",
        views.MonthlyReportExpenseUpdateView.as_view(),
        name="update_expense",
    ),
    path(
        "update_bs/<int:pk>",
        views.BalanceSheetUpdateView.as_view(),
        name="update_bs",
    ),
    path(
        "update_bs_item/<int:pk>",
        views.BalanceSheetItemUpdateView.as_view(),
        name="update_bs_item",
    ),
    # 月次収入データの個別削除
    path("delete_income/<int:pk>/", views.DeleteIncomeView.as_view(), name="delete_income"),
    # 月次収入データの一括削除
    path(
        "delete_income_by_yearmonth/",
        views.MonthlyIncomeDeleteByYearMonthView.as_view(),
        name="delete_income_by_yearmonth",
    ),
    # 月次支出データの個別削除
    path(
        "delete_expense/<int:pk>/",
        views.DeleteExpenseView.as_view(),
        name="delete_expense",
    ),
    # 月次支出データの一括削除
    path(
        "delete_expense_by_yearmonth/",
        views.MonthlyExpenseDeleteByYearMonthView.as_view(),
        name="delete_expense_by_yearmonth",
    ),
    # 貸借対照表データの個別削除
    path(
        "delete_bs/<int:pk>",
        views.BalanceSheetDeleteView.as_view(),
        name="delete_bs",
    ),
    # 貸借対照表データの一括削除
    path(
        "delete_bs_by_yearmonth/",
        views.BalanceSheetDeleteByYearMonthView.as_view(),
        name="delete_bs_by_yearmonth",
    ),
    # check
    path(
        "chk_offset/",
        views.CheckOffset.as_view(),
        name="chk_offset",
    ),
    path(
        "calcflg_check/",
        views.CalcFlgCheckList.as_view(),
        name="calcflg_check",
    ),
]
