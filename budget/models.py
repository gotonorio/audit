from django.db import models
from django.utils import timezone

from record.models import Account, Himoku


class IncomeBudget(models.Model):
    """収入予算
    - 収入予算は管理しないため、使用していない。2023-11-23
    - ToDo : 削除予定
    """

    # https://djangobrothers.com/blogs/django_datetime_localtime/
    year = models.IntegerField(verbose_name="西暦", default=timezone.now().year)
    account = models.ForeignKey(Account, verbose_name="口座名", on_delete=models.CASCADE, null=True)
    budget_income = models.IntegerField("金額", default=0)
    comment = models.CharField("備考", max_length=128, blank=True, null=True)

    def __str__(self):
        return self.account


class ExpenseBudget(models.Model):
    """支出予算モデル"""

    year = models.IntegerField(verbose_name="西暦", default=timezone.now().year)
    himoku = models.ForeignKey(Himoku, on_delete=models.CASCADE)
    budget_expense = models.IntegerField("金額", default=0)
    comment = models.CharField("備考", max_length=128, blank=True, null=True)

    def __str__(self):
        return self.himoku.himoku_name

    # 登録は同じ費目を複数登録できるようにunique制約をコメントアウトする。2023-12-29
    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(
    #             fields=["year", "himoku"], name="budget_himoku_unique"
    #         ),
    #     ]

    @classmethod
    def get_expense_budget(cls, year, ac_class):
        """支出予算0円を除く支出予算の一覧querysetを返す"""
        # 年間の支出予算
        qs = (
            cls.objects.select_related("himoku")
            .filter(year=year)
            .filter(himoku__alive=True)
            .filter(himoku__is_income=False)
            .exclude(budget_expense=0)
        )
        return qs
