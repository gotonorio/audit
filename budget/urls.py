from django.urls import path
from budget.views import views, data_views


app_name = "budget"
urlpatterns = [
    # データ表示
    # path('expenslist/', views.BudgetListView.as_view(), name='expenselist'),
    path("budget_list/", views.BudgetListView.as_view(), name="budget_list"),
    # 年次予算の作成
    path("create_budget/", data_views.CreateBudgetView.as_view(), name="create_budget"),
    # データアップデート
    path("budget_update_list/", data_views.UpdateBudgetListView.as_view(), name="budget_update_list"),
    path(
        "update_budget/<int:pk>/",
        data_views.UpdateBudgetView.as_view(),
        name="update_budget",
    ),
    path(
        "delete_budget/<int:pk>/",
        data_views.DeleteBudgetView.as_view(),
        name="delete_budget",
    ),
    path("duplicate/", data_views.DuplicateBudgetView.as_view(), name="duplicate"),
]
