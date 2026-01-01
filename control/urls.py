from django.urls import path

from control import views

app_name = "control"
urlpatterns = [
    path("control_list", views.ControlRecordListView.as_view(), name="control_list"),
    # 仮登録メニュー表示のON/OFF切替え
    path("control_update/<int:pk>/", views.ControlRecordUpdateView.as_view(), name="control_update"),
    # DBバックアップ処理
    path("backup/", views.backupDB, name="backupDB"),
]
