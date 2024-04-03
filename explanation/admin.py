from django.contrib import admin

from explanation.models import Description


class DescriptionAdmin(admin.ModelAdmin):
    list_display = [
        "no",
        "title",
        # "description",
        # "data_operation",
        "alive",
        "created_date",
    ]


admin.site.register(Description, DescriptionAdmin)
