from django.urls import path

from payment.views import views

app_name = "payment"
urlpatterns = [
    # 支払い承認リスト
    path("payment_list/", views.PaymentListView.as_view(), name="payment_list"),
    # path(
    #     "payment_list/<int:year>/<str:month>/",
    #     views.PaymentListView.as_view(),
    #     name="payment_list",
    # ),
    # 支払い承認データの編集
    path(
        "update_payment/<int:pk>/",
        views.UpdatePaymentView.as_view(),
        name="update_payment",
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
