from django.contrib import admin

from .models import Billing, BillingItem


class BillingItemAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "item_name",
        "is_billing",
        "alive",
    ]


class BillingAdmin(admin.ModelAdmin):
    list_display = [
        "transaction_date",
        "billing_item",
        "billing_amount",
        "comment",
        "author",
    ]
    ordering = ("transaction_date",)


admin.site.register(Billing, BillingAdmin)
admin.site.register(BillingItem, BillingItemAdmin)
