from django.urls import path

from explanation import views

app_name = "explanation"
urlpatterns = [
    # 表示
    path("description/", views.DescriptionView.as_view(), name="description"),
    # データ処理
    path("description_create/", views.DescriptionCreateView.as_view(), name="description_create"),
    path("description_update/<int:pk>", views.DescriptionUpdateView.as_view(), name="description_update"),
]
