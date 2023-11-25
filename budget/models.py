from django.db import models
from django.utils import timezone
from record.models import Account, Himoku


class Category(models.Model):
    """カテゴリ"""

    code = models.IntegerField(unique=True)
    name = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.name


class IncomeBudget(models.Model):
    """収入予算
    - 収入予算は管理しないため、使用していない。2023-11-23
    - ToDo : 削除予定
    """

    # https://djangobrothers.com/blogs/django_datetime_localtime/
    year = models.IntegerField(verbose_name="西暦", default=timezone.now().year)
    account = models.ForeignKey(
        Account, verbose_name="口座名", on_delete=models.CASCADE, null=True
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    budget_income = models.IntegerField("金額", default=0)
    comment = models.CharField("備考", max_length=128, blank=True, null=True)

    def __str__(self):
        return self.category.name


class ExpenseBudget(models.Model):
    """管理会計支出予算"""

    year = models.IntegerField(verbose_name="西暦", default=timezone.now().year)
    himoku = models.ForeignKey(Himoku, on_delete=models.CASCADE)
    budget_expense = models.IntegerField("金額", default=0)
    comment = models.CharField("備考", max_length=128, blank=True, null=True)

    def __str__(self):
        return self.himoku.himoku_name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["year", "himoku"], name="budget_himoku_unique"
            ),
        ]
