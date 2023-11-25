from django.urls import path
from payment import views

app_name = "payment"
urlpatterns = [
    # データ表示
    path("payment_list/", views.PaymentListView.as_view(), name="payment_list"),
    path(
        "payment_list/<int:year>/<str:month>/",
        views.PaymentListView.as_view(),
        name="payment_list",
    ),
    # データ編集
    path(
        "update_payment/<int:pk>/",
        views.UpdatePaymentView.as_view(),
        name="update_payment",
    ),
    path(
        "delete_payment/<int:pk>/",
        views.DeletePaymentView.as_view(),
        name="delete_payment",
    ),
    path(
        "create_paymentmethod/",
        views.PaymentMethodCreateView.as_view(),
        name="create_paymentmethod",
    ),
    path(
        "update_paymentmethod/<int:pk>/",
        views.PaymentMethodUpdateView.as_view(),
        name="update_paymentmethod",
    ),
]
