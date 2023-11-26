from django.contrib import admin
from budget.models import IncomeBudget, ExpenseBudget


class IncomeBudgetAdmin(admin.ModelAdmin):
    list_display = ["year", "account", "budget_income", "comment"]
    ordering = ("year",)


class ExpenseBudgetAdmin(admin.ModelAdmin):
    list_display = ["year", "himoku", "budget_expense", "comment"]
    ordering = ("year",)


admin.site.register(IncomeBudget, IncomeBudgetAdmin)
admin.site.register(ExpenseBudget, ExpenseBudgetAdmin)
