from django.db import models
from record.models import Himoku


class ControlRecord(models.Model):
    """プロジェクトのコントロール用定数を定義"""

    # 仮登録メニューの表示/非表示コントロール
    tmp_user_flg = models.BooleanField(verbose_name="仮登録", default=False)
    # 管理費+緑地維持管理費の年間収入額
    annual_management_fee = models.IntegerField(verbose_name="管理費収入額", default=0)
    # 緑地維持管理費の年間収入額
    annual_greenspace_fee = models.IntegerField(verbose_name="緑地維持管理費収入額", default=0)
    # 相殺処理する費目名
    to_offset = models.ForeignKey(
        Himoku, verbose_name="費目名", on_delete=models.CASCADE, blank=True, null=True
    )
    # データ削除フラグの表示/非表示コントロールを追加（2025年12月1日）
    delete_data_flg = models.BooleanField(verbose_name="データ削除", default=False)

    @classmethod
    def show_tmp_user_menu(cls):
        return cls.objects.get("tmp_user_flg")

    @classmethod
    def get_offset_himoku(cls):
        """相殺処理する費目名を返す
        - 総裁処理する費目は一つだけの想定
        """
        offset_himoku = cls.objects.values("to_offset__himoku_name").first()
        return offset_himoku["to_offset__himoku_name"]
