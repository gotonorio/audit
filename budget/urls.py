from django.urls import path

from budget.views import data_views, views

app_name = "budget"
urlpatterns = [
    # ------------------------------------------------------------------------
    # データ表示
    # ------------------------------------------------------------------------
    path("budget_list/", views.BudgetListView.as_view(), name="budget_list"),
    path("duplicate/", data_views.DuplicateBudgetView.as_view(), name="duplicate"),
    # ------------------------------------------------------------------------
    # データ編集
    # ------------------------------------------------------------------------
    # 年次予算のcreate
    path("create_budget/", data_views.CreateKanriBudgetView.as_view(), name="create_budget"),
    path(
        "create_shuuzen_budget/", data_views.CreateShuuzenBudgetView.as_view(), name="create_shuuzen_budget"
    ),
    path(
        "create_parking_budget/", data_views.CreateParkingBudgetView.as_view(), name="create_parking_budget"
    ),
    # データアップデート
    path("budget_update_list/", data_views.UpdateBudgetListView.as_view(), name="budget_update_list"),
    path("update_budget/<int:pk>/", data_views.UpdateBudgetView.as_view(), name="update_budget"),
    path("delete_budget/<int:pk>/", data_views.DeleteBudgetView.as_view(), name="delete_budget"),
]
