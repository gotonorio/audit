from django.contrib import admin

from control.models import ControlRecord, FiscalLock


class ControlRecordAdmin(admin.ModelAdmin):
    list_display = [
        "tmp_user_flg",
        "annual_management_fee",
        "annual_greenspace_fee",
        "delete_data_flg",
        "to_offset",
    ]


admin.site.register(ControlRecord, ControlRecordAdmin)


class FiscalLockAdmin(admin.ModelAdmin):
    list_display = [
        "year",
        "is_locked",
        "last_closed_month",
        "updated_at",
    ]


admin.site.register(FiscalLock, FiscalLockAdmin)
