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


class FiscalLock(models.Model):
    """決算・月次締め管理モデル
    クラセルの場合、管理会社側で年次決算前の「月次収入・支出」データの修正が
    行われる可能性があるため、決算を確認してから決算ロックを行う。
    一応、月次決算対応のための要素（last_closed_month）を入れておく。
    """

    year = models.IntegerField(
        "年度", unique=True, help_text="4月始まりの場合、2025年4月〜2026年3月は『2025』年度"
    )
    is_locked = models.BooleanField(
        "決算確定（ロック）",
        default=False,
        help_text="チェックを入れると、この年度のデータは削除・編集不可になります",
    )
    last_closed_month = models.IntegerField(
        "最終締め月", default=0, help_text="例：9月まで締めた場合は『9』。0は未締め"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "決算・締め状態管理"
        verbose_name_plural = "決算・締め状態管理"

    def __str__(self):
        status = "確定済" if self.is_locked else f"{self.last_closed_month}月まで締"
        return f"{self.year}年度 ({status})"

    @classmethod
    def is_period_frozen(cls, target_date):
        """
        指定された日付（1月〜12月年度）がロックされているか判定する
        """
        target_year = target_date.year
        target_month = target_date.month

        # 1. 年度の一致（1月〜12月なら target_year がそのまま年度）
        lock_status = cls.objects.filter(year=target_year).first()

        if not lock_status:
            return False  # 設定がなければロックされていないとみなす

        # 2. 年度全体がロック（決算確定）されている場合
        if lock_status.is_locked:
            return True

        # 3. 月次締めの判定
        # その年度の「最終締め月」以下の月であればロックされているとみなす
        if target_month <= lock_status.last_closed_month:
            return True

        return False

    # @classmethod
    # def is_period_frozen(cls, target_date):
    #     """
    #     指定された日付（当年4月〜翌年3月年度）がロックされているか判定する
    #     """
    #     # 会計年度の計算 (4月始まりの例)
    #     year = target_date.year
    #     month = target_date.month
    #     fiscal_year = year if month >= 4 else year - 1

    #     lock_status = cls.objects.filter(year=fiscal_year).first()
    #     if not lock_status:
    #         return False

    #     # 年度全体がロックされている場合
    #     if lock_status.is_locked:
    #         return True

    #     # 月次締めの判定 (年度内での月比較)
    #     # 4月始まりの場合、月を比較しやすい数値に変換する例
    #     def month_to_rank(m):
    #         return m if m >= 4 else m + 12

    #     if month_to_rank(month) <= month_to_rank(lock_status.last_closed_month):
    #         return True

    #     return False
