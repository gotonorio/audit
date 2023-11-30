from django.urls import path
from record.views import views
from record.views import data_operate

app_name = "record"
urlpatterns = [
    # データ表示
    path(
        "transaction_list/",
        views.TransactionListView.as_view(),
        name="transaction_list",
    ),
    path(
        "transaction_original_list/",
        views.TransactionOriginalListView.as_view(),
        name="transaction_original_list",
    ),
    # update後の遷移url
    path(
        "transaction_list/<int:year>/<str:month>/<int:ac_class>/<int:list_order>/",
        views.TransactionListView.as_view(),
        name="transaction_list",
    ),
    # # 資金移動のチェック
    # path('chk_transfer/', views.CheckTransferFoundView.as_view(), name='chk_transfer'),
    # 前受金データチェック
    path("chk_maeuke/", views.CheckMaeukeDataView.as_view(), name="chk_maeuke"),
    # データ編集
    path(
        "transaction_create/",
        data_operate.TransactionCreateView.as_view(),
        name="transaction_create",
    ),
    path(
        "transaction_update/<int:pk>/",
        data_operate.TransactionUpdateView.as_view(),
        name="transaction_update",
    ),
    path(
        "transaction_delete/<int:pk>/",
        data_operate.TransactionDeleteView.as_view(),
        name="transaction_delete",
    ),
    path(
        "himoku_create/", data_operate.HimokuCreateView.as_view(), name="himoku_create"
    ),
    path(
        "himoku_list/", data_operate.HimokuListView.as_view(), name="himoku_list"
    ),
    path(
        "himoku_update/<int:pk>/",
        data_operate.HimokuUpdateView.as_view(),
        name="himoku_update",
    ),
    path(
        "requester_create/",
        data_operate.TransferRequesterCreateView.as_view(),
        name="requester_create",
    ),
    path(
        "requester_update/<int:pk>",
        data_operate.TransferRequesterUpdateView.as_view(),
        name="requester_update",
    ),
    path(
        "transaction_offset_create/<int:pk>/",
        data_operate.TransactionOffsetCreateView.as_view(),
        name="transaction_offset_create",
    ),
    path(
        "transaction_divide/<int:pk>",
        data_operate.TransactionDivideCreateView.as_view(),
        name="transaction_divide",
    ),
    #     path('transaction_divide/(?P<pk>[0-9]+)/$',
    #          data_operate.TransactionDivideCreateView.as_view(), name='transaction_divide'),
    path(
        "read_himoku_csv/",
        data_operate.HimokuCsvReadView.as_view(),
        name="read_himoku_csv",
    ),
]
