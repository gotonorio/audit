from django.urls import path

from record.views import data_operate, views

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
        data_operate.TransactionCreateView.as_view(),
        name="transaction_create",
    ),
    # 入出金明細データの修正・削除（削除はしない？）
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
    # マスタデータ関係
    path("himoku_create/", data_operate.HimokuCreateView.as_view(), name="himoku_create"),
    path("himoku_list/", data_operate.HimokuListView.as_view(), name="himoku_list"),
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
    path(
        "read_himoku_csv/",
        data_operate.HimokuCsvReadView.as_view(),
        name="read_himoku_csv",
    ),
    path(
        "approval_text_create/",
        data_operate.ApprovalTextCreateView.as_view(),
        name="approval_text_create",
    ),
    path(
        "approval_text_update/<int:pk>",
        data_operate.ApprovalTextUpdateView.as_view(),
        name="approval_text_update",
    ),
    # 管理費等請求一覧リスト表示
    path("claim_list/", views.ClaimDataListView.as_view(), name="claim_list"),
    path(
        "claim_list/<int:year>/<int:month>/<str:claim_type>",
        views.ClaimDataListView.as_view(),
        name="claim_list",
    ),
    path("claim_update/<int:pk>", data_operate.ClaimdataUpdateView.as_view(), name="claim_update"),
]
