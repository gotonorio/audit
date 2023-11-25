from django.urls import path

from register.views import views
from register.views import user_views


app_name = "register"
urlpatterns = [
    path("", views.Login.as_view(), name="login"),
    path("login/", views.Login.as_view(), name="login"),
    path("logout/", views.Logout.as_view(), name="logout"),
    path("mypage/", views.MypageView.as_view(), name="mypage"),
    path("master_page/", views.MasterPageView.as_view(), name="master_page"),
    # ユーザー登録・修正
    path("signup/", user_views.TempUserCreateView.as_view(), name="signup"),
    path("signup_done/", user_views.TempUserDoneView.as_view(), name="done_temp_user"),
    path("user_list/", user_views.UserListView.as_view(), name="user_list"),
    path(
        "user_update/<int:pk>/",
        user_views.UserManagementView.as_view(),
        name="user_update",
    ),
    path(
        "pwd_update/<int:pk>/",
        user_views.UserPasswordUpdate.as_view(),
        name="pwd_update",
    ),
    # ユーザー削除
    path(
        "delete_user/<int:pk>", user_views.DeleteUserView.as_view(), name="delete_user"
    ),
]
