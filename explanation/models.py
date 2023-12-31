from django.db import models
from django.utils import timezone


class Description(models.Model):
    """説明モデル"""

    no = models.IntegerField(default=0)
    title = models.CharField(verbose_name="タイトル", max_length=32)
    description = models.TextField(verbose_name="説明文")
    data_operation = models.BooleanField(default=False)
    alive = models.BooleanField(verbose_name="有効", default=True)
    created_date = models.DateTimeField(verbose_name="作成日", default=timezone.now)

    def __str__(self):
        return self.title
