from django.contrib import admin

from payment.models import Payment, PaymentCategory, PaymentMethod


class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "payment_date",
        "himoku",
        "payment_destination",
        "payment",
        "summary",
    ]
    ordering = ("payment_date",)


class PaymentCategoryAdmin(admin.ModelAdmin):
    list_display = [
        "payment_name",
        "comment",
    ]
    ordering = ("payment_name",)


class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = [
        "ac_class",
        "payment_category",
        "himoku_name",
        "payee",
        "amounts",
        "banking_fee",
        "account_description",
        "comment",
    ]
    ordering = ("ac_class", "payment_category")


admin.site.register(Payment, PaymentAdmin)
admin.site.register(PaymentCategory, PaymentCategoryAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
