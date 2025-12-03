from django.db import models
from record.models import Himoku


class ControlRecord(models.Model):
    """プロジェクトのコントロール用定数を定義
    - tmp_user_flg : 仮登録メニューの表示/非表示（ユーザー登録させる場合に表示させる。普段は非表示とする）
    - annual_management_fee : 管理費収入額（予算実績対比表で管理会計の予算オーバー防止のために使用）
    - annual_greenspace_fee : 緑地維持管理費収入額（予算実績対比表で管理会計の予算オーバー防止のために使用）
    - to_offset : 相殺処理する費目名（収納代行会社：三菱UFJファクター株式会社による振替時に自動的に支出される手数料項目）
    - delete_data_flg : データ削除フラグの表示/非表示（データ取り込み時に年月を指定する場合、年月のミスが起こり得るため、
                        データ削除を許可する場合に表示させる。普段は非表示とする）
    """

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

    @classmethod
    def get_delete_flg(cls):
        """データ削除フラグの表示/非表示を返す"""
        return cls.objects.values("delete_data_flg")[0]["delete_data_flg"]
