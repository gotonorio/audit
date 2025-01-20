from django.contrib import admin

from record.models import (
    Account,
    AccountingClass,
    ApprovalCheckData,
    Bank,
    ClaimData,
    Himoku,
    Transaction,
    TransferRequester,
)


class BankAdmin(admin.ModelAdmin):
    list_display = ["code", "bank_name", "alive"]
    ordering = ("code",)


class AccountAdmin(admin.ModelAdmin):
    list_display = [
        "account_name",
        "branch_number",
        "account_number",
        "account_type",
        "bank",
        "alive",
        "start_day",
        "start_ammount",
    ]
    ordering = ("bank",)


class AccountingClassAdmin(admin.ModelAdmin):
    list_display = ["code", "accounting_name"]
    ordering = ("code",)


class HimokuAdmin(admin.ModelAdmin):
    list_display = ["code", "himoku_name", "alive", "aggregate_flag", "is_approval", "is_community"]
    ordering = ("code",)


class TransferRequesterAdmin(admin.ModelAdmin):
    list_display = ["requester", "himoku", "comment"]
    ordering = ("requester",)


class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "account",
        "is_income",
        "is_manualinput",
        "transaction_date",
        "amount",
        "himoku",
        "balance",
        "description",
        "is_approval",
        "is_billing",
    ]
    ordering = ("transaction_date",)


class ApprovalCheckDataAdmin(admin.ModelAdmin):
    list_display = ["atext", "comment", "alive"]


class ClaimDataAdmin(admin.ModelAdmin):
    list_display = ["claim_date", "claim_type", "room_no", "name", "amount", "comment"]
    ordering = ("claim_type", "claim_date")


# Register your models here.
admin.site.register(Bank, BankAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(AccountingClass, AccountingClassAdmin)
admin.site.register(Himoku, HimokuAdmin)
admin.site.register(TransferRequester, TransferRequesterAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(ApprovalCheckData, ApprovalCheckDataAdmin)
admin.site.register(ClaimData, ClaimDataAdmin)
