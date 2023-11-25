from django.db import models


class ControlRecord(models.Model):
    """プロジェクトのコントロール用定数を定義"""

    # 仮登録メニューの表示/非表示コントロール
    tmp_user_flg = models.BooleanField(verbose_name="仮登録", default=False)
    # 管理費+緑地維持管理費の年間収入額
    annual_management_fee = models.IntegerField(verbose_name="管理費収入額", default=0)
    # 緑地維持管理費の年間収入額
    annual_greenspace_fee = models.IntegerField(verbose_name="緑地維持管理費収入額", default=0)

    # add your control variable

    @classmethod
    def show_tmp_user_menu(cls):
        return cls.objects.get("tmp_user_flg")
