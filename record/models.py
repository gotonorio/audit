import logging

from django.conf import settings
from django.contrib.auth import get_user_model

# from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone

user = get_user_model()
logger = logging.getLogger(__name__)


class Bank(models.Model):
    """銀行マスタ"""

    code = models.CharField(verbose_name="金融機関コード", max_length=4, unique=True)
    bank_name = models.CharField(verbose_name="銀行名", max_length=64, unique=True)
    alive = models.BooleanField(verbose_name="有効", default=True)

    def __str__(self):
        return self.bank_name


class Account(models.Model):
    """口座マスタ"""

    account_name = models.CharField(verbose_name="口座名", max_length=32)
    branch_number = models.CharField(verbose_name="支店番号", max_length=10)
    account_number = models.CharField(verbose_name="口座番号", max_length=16, unique=True)
    account_type = models.CharField(verbose_name="口座種類", max_length=16)
    bank = models.ForeignKey(Bank, verbose_name="銀行名", on_delete=models.CASCADE)
    alive = models.BooleanField(verbose_name="有効", default=True)
    start_day = models.DateField(verbose_name="開始日", blank=True, null=True)
    start_ammount = models.IntegerField(verbose_name="開始残高", blank=True, null=True)

    def __str__(self):
        return self.account_name + " (" + self.account_number + ")"

    @classmethod
    def get_account_obj(cls, ac_name):
        """口座名からそのオブジェクトを返す"""
        try:
            qs = cls.objects.get(account_name=ac_name)
        except cls.DoesNotExist:
            qs = None
        return qs


class AccountingClass(models.Model):
    """会計区分マスタ（Kurasel導入で追加）"""

    code = models.IntegerField(verbose_name="コード", unique=True)
    accounting_name = models.CharField(verbose_name="会計区分名", max_length=32, unique=True)

    def __str__(self):
        return self.accounting_name

    @classmethod
    def get_accountingclass_obj(cls, accounting_class):
        """会計区分名からそのオブジェクトを返す"""
        qs = cls.objects.get(accounting_name=accounting_class)
        return qs

    def get_accountingclass_name(ac_pk):
        try:
            qs = AccountingClass.objects.get(pk=ac_pk)
            ac_name = qs.accounting_name
        except AccountingClass.DoesNotExist:
            ac_name = None

        return ac_name

    @classmethod
    def get_class_name(cls, shortname):
        """概略名から推測した管理費会計の会計区分名を返す"""
        try:
            qs = cls.objects.filter(accounting_name__contains=shortname)
            if qs:
                class_name = qs[0].accounting_name
            else:
                class_name = None
        except AccountingClass.DoesNotExist:
            class_name = None
        return class_name


class Himoku(models.Model):
    """費目マスタ"""

    code = models.IntegerField(verbose_name="コード", unique=True)
    himoku_name = models.CharField(verbose_name="費目名", max_length=64)
    is_income = models.BooleanField(verbose_name="入金費目", default=False)
    alive = models.BooleanField(verbose_name="有効", default=True)
    aggregate_flag = models.BooleanField(verbose_name="集計", default=True)
    # Kurasel導入で追加
    accounting_class = models.ForeignKey(
        AccountingClass, on_delete=models.CASCADE, blank=True, null=True
    )
    is_approval = models.BooleanField(verbose_name="承認必要", default=True)
    is_default = models.BooleanField(verbose_name="デフォルト", default=False)

    def __str__(self):
        return self.himoku_name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["himoku_name", "accounting_class"], name="himoku_unique"
            ),
            models.UniqueConstraint(
                fields=["is_default"],
                condition=models.Q(is_default=True),
                name="default_himoku_unique",
            ),
        ]

    @classmethod
    def get_himoku_name(cls, code):
        """Selectされた費目コードから費目名を返す
        - ModelFormのChoiceFieldはprimary key(id)を返す。
        """
        if code:
            qs = cls.objects.get(id=code)
            ret = qs.himoku_name
        else:
            ret = ""
        return ret

    @classmethod
    def get_himoku_code(cls, name):
        """費目名からcodeを返す"""
        if name:
            try:
                qs = cls.objects.get(himoku_name=name)
                ret = qs.code
            except cls.DoesNotExist:
                ret = None
        else:
            ret = None
        return ret

    @classmethod
    def get_himoku_obj(cls, himoku, ac_class):
        """費目名からそのオブジェクトを返す"""
        if ac_class.upper() == "ALL":
            try:
                qs = cls.objects.get(himoku_name=himoku)
            except cls.DoesNotExist:
                qs = None
        else:
            try:
                qs = cls.objects.get(himoku_name=himoku, accounting_class=ac_class)
            except cls.DoesNotExist:
                qs = None
        return qs

    @classmethod
    def get_default_himoku(cls):
        """デフォルト費目オブジェクトを返す。
        - 前提として、default費目が1つだけ設定されていること。
        - is_defaultはUniqueConstraintでuniqueを担保しているためget()を使う。
        - 費目名は、呼び出し側で default_himoku.himoku_nameとする。
        - https://qiita.com/Bashi50/items/9e1d62c4159f065b662b
        """
        try:
            default_himoku = cls.objects.get(is_default=True)
            return default_himoku
        except Himoku.DoesNotExist:
            return None
        except Himoku.MultipleObjectsReturned:
            return None

    @classmethod
    def get_himoku_list(cls):
        """有効な費目名をリストで返す"""
        himoku_list = []
        himoku_list = cls.objects.filter(alive=True).values_list(
            "himoku_name", flat=True
        )
        return himoku_list

    @classmethod
    def save_himoku(cls, data_list):
        """費目マスタデータが存在しない場合だけDB登録する"""
        rtn = True
        error_list = []
        for item in data_list:
            try:
                ac_class = AccountingClass.get_accountingclass_obj(item[0])
                cls.objects.get_or_create(
                    accounting_class=ac_class,
                    code=item[1],
                    himoku_name=item[2],
                    defaults={
                        "accounting_class": ac_class,
                        "code": item[1],
                        "himoku_name": item[2],
                        "is_income": False,
                        "alive": True,
                        "is_approval": True,
                        "aggregate_flag": True,
                    },
                )
            except Exception as e:
                logger.error(e)
                error_list.append(f"{item[0]}-{item[1]}-{item[2]}")
                rtn = False
        return rtn, error_list


class TransferRequester(models.Model):
    """Kuraselの振込依頼人データと費目名を関連付けるためのモデル"""

    requester = models.CharField(
        verbose_name="振込依頼人名", max_length=64, blank=True, null=True
    )
    himoku = models.ForeignKey(
        Himoku, verbose_name="費目名", on_delete=models.CASCADE, blank=True, null=True
    )
    comment = models.CharField(verbose_name="備考", max_length=64, blank=True, null=True)

    def __str__(self):
        return self.requester

    @staticmethod
    def get_requester_obj():
        qs = TransferRequester.objects.all()
        obj_list = [obj for obj in qs]
        return obj_list


class Transaction(models.Model):
    """取引明細データ
    費目が明確でないので、入出金を区別するフィールドが必要。
    入出金種別を「入金/出金」だけにするため、is_incomeフィールドを追加。2023-03-04
    """

    account = models.ForeignKey(
        Account, verbose_name="口座名", on_delete=models.CASCADE, null=True
    )
    is_income = models.BooleanField(verbose_name="入金flg", default=False)
    transaction_date = models.DateField(verbose_name="取引日")
    ammount = models.IntegerField(verbose_name="金額", default=0)
    himoku = models.ForeignKey(
        Himoku, verbose_name="費目名", on_delete=models.CASCADE, null=True
    )
    requesters_name = models.CharField(verbose_name="振込依頼人名", max_length=64, default="")
    description = models.CharField(verbose_name="摘要", max_length=64, default="")
    balance = models.IntegerField(verbose_name="残高", null=True, blank=True)
    author = models.ForeignKey(
        user, verbose_name="記録者", on_delete=models.CASCADE, null=True
    )
    created_date = models.DateTimeField(verbose_name="作成日", default=timezone.now)
    delete_flg = models.BooleanField(default=False)
    calc_flg = models.BooleanField(default=True)
    # 2023-08-20 前受金を分別するための手入力データフラグ。
    # 合算入力された取引データの相殺データと、分割して追加入力したデータではTrueにする。
    is_manualinput = models.BooleanField(default=False)

    def __str__(self):
        return self.himoku.himoku_name

    # def delete(self):
    #     """ delete関数を論理削除にするためにオーバーライド
    #     - DeleteViewで削除処理すると、レコードは削除せずdelete_flgをTrueにする。
    #     """
    #     self.delete_flg = True
    #     self.save()

    @staticmethod
    def get_maeuke(tstart, tend):
        """通帳データの前受金合計を返す
        他の関数（stattic method）に依存するため、インスタンス関数とする。
        """
        # 前受金の費目id
        id = Himoku.get_himoku_obj(settings.MAEUKE, "all")
        total = 0
        qs = Transaction.objects.filter(transaction_date__range=[tstart, tend]).filter(
            himoku=id
        )
        for i in qs:
            total += i.ammount
        return total

    @staticmethod
    def all_total(sql):
        """通帳データの合計"""
        total_deposit = 0
        total_withdrawals = 0
        for data in sql:
            # 「資金移動」費目では収入と支出の両パターンがあるため、is_incomeを使う。
            if data.is_income:
                total_deposit += data.ammount
            else:
                total_withdrawals += data.ammount
        return total_deposit, total_withdrawals

    #
    # for Kurasel
    #
    @staticmethod
    def calc_total(sql):
        """通帳データの合計計算は計算対象項目のみ"""
        total_deposit = 0
        total_withdrawals = 0
        for data in sql:
            if data.calc_flg:
                # 「資金移動」費目では収入と支出の両パターンがあるため、is_incomeを使う。
                if data.is_income:
                    total_deposit += data.ammount
                else:
                    total_withdrawals += data.ammount
        return total_deposit, total_withdrawals

    @classmethod
    def get_qs_pb(cls, tstart, tend, account, ac_class, deposit_flg, manualinput):
        """querysetを返す。
        資金移動は含むので、必要なら呼び出し側で処理する。
        tstart/tend : 抽出期間。
        account : 口座名（Kuraselの場合は1口座となる。
        ac_class : 費目名に紐づいた会計区分。
        deposit_flg : 入金はTrue、出金はFalse。""の場合は入出金を抽出する。
        manualinput : 手入力データを含めて抽出の場合はTrue。
        manualinput=Trueの場合、補正データを表示する。Falseの場合、Kuraselの入出金明細データだけを表示。
        """
        qs_pb = cls.objects.all().select_related("himoku")
        if manualinput:
            qs_pb = qs_pb.filter(transaction_date__range=[tstart, tend])
        else:
            qs_pb = qs_pb.filter(transaction_date__range=[tstart, tend]).filter(
                is_manualinput=False
            )
        if deposit_flg == "income":
            # 収入を抽出。
            qs_pb = qs_pb.filter(is_income=True)
        elif deposit_flg == "expense":
            # 支出を抽出
            qs_pb = qs_pb.filter(is_income=False)
            # 修繕費（旧保管口座の修繕会計分）を除外【変更】2022-7-24
            # qs_pb = qs_pb.exclude(himoku__himoku_name='修繕工事費')
        # 口座種類でfilter
        if account != "":
            qs_pb = qs_pb.filter(account=account)
        # 費目の会計区分でfilter
        if ac_class != "":
            qs_pb = qs_pb.filter(himoku__accounting_class=ac_class)
        return qs_pb

    # @staticmethod
    # def kurasel_pb_total(sql, approval):
    #     """ 通帳データの合計計算
    #     - approval=True : 承認申請が必要な費目のみの合計を返す。
    #     """
    #     total_pb = 0
    #     if approval:
    #         for d in sql:
    #             if d.himoku.is_approval:
    #                 total_pb += d.ammount
    #     else:
    #         for d in sql:
    #             total_pb += d.ammount

    #     return total_pb

    @classmethod
    def dwd_from_kurasel(cls, data, paymenmethod_list, requester_list, default_himoku):
        """kurasel_translatorからDeposits and withdrawals（入出金明細データ）を読み込む
        - 種類、日付、金額、振り込み依頼人でget_or_createする。
        - 口座は管理会計に決め打ち(id=3)。
        - 費目はdefaultの費目オブジェクト。
        - 勘定科目・費目は手入力となる。
        """
        # 記録者
        author_obj = user.objects.get(id=data["author"])

        # error flag
        error_list = []
        rtn = True
        # 取り込んだデータの保存処理。
        for item in data["data_list"]:
            income = False
            himoku_chk = True
            # 入金の場合、入金フラグをTrue。費目はdefault費目とする。
            if item[0] == "入金":
                income = True
                himoku_obj = default_himoku
            # 出金の場合、振込依頼者、摘要で費目を特定する。
            else:
                # 最初に費目をdefault費目にセットする。
                himoku_obj = default_himoku
                # (1)「支払先」で費目を推定する。
                for requester in requester_list:
                    if item[4] == requester.requester:
                        himoku_obj = requester.himoku
                        himoku_chk = False
                        break
                # (2)「支払先」で推定できない場合「摘要」で費目を推定する。
                if himoku_chk:
                    for paymentmethod in paymenmethod_list:
                        if item[5] == paymentmethod.account_description:
                            himoku_obj = paymentmethod.himoku_name
                            break
            # 保存処理（日付、金額、振込依頼人名が一致する場合、上書き保存しない）
            try:
                cls.objects.get_or_create(
                    transaction_date=item[1],
                    ammount=item[2],
                    requesters_name=item[4],
                    defaults={
                        "account": Account.objects.all().first(),
                        "is_income": income,
                        "transaction_date": item[1],
                        "himoku": himoku_obj,
                        "ammount": int(item[2]),
                        "balance": item[3],
                        "requesters_name": item[4],
                        "description": item[5],
                        "author": author_obj,
                    },
                )
            except Exception as e:
                logger.error(e)
                error_list.append(item[4])
                rtn = False
        return rtn, error_list
