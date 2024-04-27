from django.contrib import admin

from .models import BalanceSheet, BalanceSheetItem, ReportTransaction


class ReportTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "account",
        "accounting_class",
        "transaction_date",
        "ammount",
        "himoku",
        "description",
        "is_netting",
        "is_miharai",
        "is_manualinput",
    ]
    ordering = ("transaction_date",)


class BalanceSheetItemAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "ac_class",
        "item_name",
        "is_asset",
    ]


class BalanceSheetAdmin(admin.ModelAdmin):
    list_display = [
        "monthly_date",
        "amounts",
        "item_name",
        "comment",
    ]


admin.site.register(ReportTransaction, ReportTransactionAdmin)
admin.site.register(BalanceSheetItem, BalanceSheetItemAdmin)
admin.site.register(BalanceSheet, BalanceSheetAdmin)
