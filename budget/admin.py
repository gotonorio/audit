from django.contrib import admin
from budget.models import Category, IncomeBudget, ExpenseBudget


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]
    ordering = ("code",)


class IncomeBudgetAdmin(admin.ModelAdmin):
    list_display = ["year", "account", "category", "budget_income", "comment"]
    ordering = ("year", "category")


class ExpenseBudgetAdmin(admin.ModelAdmin):
    list_display = ["year", "himoku", "budget_expense", "comment"]
    ordering = ("year",)


admin.site.register(Category, CategoryAdmin)
admin.site.register(IncomeBudget, IncomeBudgetAdmin)
admin.site.register(ExpenseBudget, ExpenseBudgetAdmin)
