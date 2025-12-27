from django.urls import path

from record import views

app_name = "record"
urlpatterns = [
    # 入出金細目データ表示
    path(
        "transaction_list/",
        views.TransactionListView.as_view(),
        name="transaction_list",
    ),
    path(
        "transaction_list/<int:year>/<int:month>/<int:list_order>/<int:himoku_id>/",
        views.TransactionListView.as_view(),
        name="transaction_list",
    ),
    path(
        "transaction_original_list/",
        views.TransactionOriginalListView.as_view(),
        name="transaction_original_list",
    ),
    # 前受金データチェック
    path("chk_maeuke/", views.CheckMaeukeDataView.as_view(), name="chk_maeuke"),
    # 入出金明細データの読込み
    path(
        "transaction_create/",
        views.TransactionCreateView.as_view(),
        name="transaction_create",
    ),
    # 入出金明細データの修正・削除（削除はしない？）
    path(
        "transaction_update/<int:pk>/",
        views.TransactionUpdateView.as_view(),
        name="transaction_update",
    ),
    path(
        "transaction_delete/<int:pk>/",
        views.TransactionDeleteView.as_view(),
        name="transaction_delete",
    ),
    # マスタデータ関係
    path("himoku_create/", views.HimokuCreateView.as_view(), name="himoku_create"),
    path("himoku_list/", views.HimokuListView.as_view(), name="himoku_list"),
    path(
        "himoku_update/<int:pk>/",
        views.HimokuUpdateView.as_view(),
        name="himoku_update",
    ),
    path(
        "requester_create/",
        views.TransferRequesterCreateView.as_view(),
        name="requester_create",
    ),
    path(
        "requester_update/<int:pk>",
        views.TransferRequesterUpdateView.as_view(),
        name="requester_update",
    ),
    path(
        "transaction_offset_create/<int:pk>/",
        views.TransactionOffsetCreateView.as_view(),
        name="transaction_offset_create",
    ),
    path(
        "transaction_divide/<int:pk>",
        views.TransactionDivideCreateView.as_view(),
        name="transaction_divide",
    ),
    path(
        "read_himoku_csv/",
        views.HimokuCsvReadView.as_view(),
        name="read_himoku_csv",
    ),
    # 管理費等請求一覧リスト表示
    path("claim_list/", views.ClaimDataListView.as_view(), name="claim_list"),
    path(
        "claim_list/<int:year>/<int:month>/<str:claim_type>",
        views.ClaimDataListView.as_view(),
        name="claim_list",
    ),
]
