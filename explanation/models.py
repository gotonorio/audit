from django.db import models
from django.utils import timezone


class Description(models.Model):
    """説明モデル
    - no: プルダウンメニューの表示順
    - title: ヘルプタイトル
    - description: 説明文（markdown記法）
    - alive: 表示の有効/無効用フラグ
    - data_operation: 未使用（何のために設定したのか忘れた）
    """

    no = models.IntegerField(default=0, unique=True)
    title = models.CharField(verbose_name="タイトル", max_length=32)
    description = models.TextField(verbose_name="説明文")
    data_operation = models.BooleanField(default=False)
    alive = models.BooleanField(verbose_name="有効", default=True)
    created_date = models.DateTimeField(verbose_name="作成日", default=timezone.now)

    def __str__(self):
        return self.title

    @classmethod
    def get_description_list(cls):
        """説明文一覧を返す"""
        qs = cls.objects.all().order_by("no")
        return qs
