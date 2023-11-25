from django.contrib import admin
from control.models import ControlRecord


class ControlRecordAdmin(admin.ModelAdmin):
    list_display = [
        "tmp_user_flg",
        "annual_management_fee",
        "annual_greenspace_fee",
    ]


admin.site.register(ControlRecord, ControlRecordAdmin)
