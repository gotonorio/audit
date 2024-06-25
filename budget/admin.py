from django.contrib import admin

from budget.models import ExpenseBudget


class ExpenseBudgetAdmin(admin.ModelAdmin):
    list_display = ["year", "himoku", "budget_expense", "comment"]
    ordering = ("year",)


admin.site.register(ExpenseBudget, ExpenseBudgetAdmin)
