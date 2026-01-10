import datetime
import logging
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from passbook.services import select_period

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
    start_amount = models.IntegerField(verbose_name="開始残高", blank=True, null=True)

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
    def get_accountingclass_obj(cls, accounting_class_name):
        """会計区分名からそのオブジェクトを返す
        例えば、町内会会計の項目を除く場合は下記のようにする。
            obj = AccountingClass.get_accountingclass_obj(AccountingClass.get_class_name("町内会"))
            qs = qs.exclude(himoku__accounting_class=obj.pk)
        """
        qs = cls.objects.get(accounting_name=accounting_class_name)
        return qs

    @classmethod
    def get_accountingclass_name(cls, ac_pk) -> str:
        try:
            qs = cls.objects.get(pk=ac_pk)
            ac_name = qs.accounting_name
        except AccountingClass.DoesNotExist:
            ac_name = ""

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
    """費目マスタ
    - aggregate_flag: 資金移動などの場合はFalseとする。Falseの場合は表示するが、合計計算では無視する。
    """

    code = models.IntegerField(verbose_name="コード", unique=True)
    himoku_name = models.CharField(verbose_name="費目名", max_length=64)
    is_income = models.BooleanField(verbose_name="入金費目", default=False)
    alive = models.BooleanField(verbose_name="有効", default=True)
    aggregate_flag = models.BooleanField(verbose_name="集計", default=True)
    # Kurasel導入で追加
    accounting_class = models.ForeignKey(AccountingClass, on_delete=models.CASCADE, blank=True, null=True)
    is_approval = models.BooleanField(verbose_name="承認必要", default=True)
    is_default = models.BooleanField(verbose_name="デフォルト", default=False)
    is_community = models.BooleanField(verbose_name="町内会", default=False)
    comment = models.CharField(verbose_name="備考", max_length=64, blank=True, default="")

    def __str__(self):
        return self.himoku_name + " (" + self.accounting_class.accounting_name[:1] + ")"

    class Meta:
        """ユニーク制約
        - 費目名は会計区分毎にユニークとする。
        - デフォルトフラグ（Kuraselから取り込む時のデフォルト費目名）のTrueはユニークとする。
        """

        constraints = [
            models.UniqueConstraint(fields=["himoku_name", "accounting_class"], name="himoku_unique"),
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
        """費目名からそのオブジェクトを返す
        - 費目名はKuraselに合わせる。「他会計からの受け入れ」は独自の費目となる。
        - 費目名が存在しない場合はNoneを返す。
        - 複数の場合はデフォルト費目名を返す。ToDo : 「default費目」は出金費目になっている。収入の場合表示されない!!
        """
        try:
            qs = cls.objects.get(
                alive=True,
                himoku_name=himoku,
                accounting_class__accounting_name__contains=ac_class,
            )
        except cls.DoesNotExist:
            qs = None
        except cls.MultipleObjectsReturned:
            qs = cls.get_default_himoku()
        return qs

    @classmethod
    def get_default_himoku(cls):
        """デフォルト費目オブジェクトを返す。
        - 前提として、default費目が「収入」「支出」でそれぞれ1つだけ設定されている。
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
    def get_himoku_list(cls, ac_class_name=None):
        """有効な費目名をリストで返す"""
        himoku_list = []
        himoku_list = (
            cls.objects.filter(accounting_class__accounting_name=ac_class_name)
            # .filter(alive=True)
            .values_list("himoku_name", flat=True)
        )
        return list(himoku_list)

    @classmethod
    def get_without_community(cls):
        """町内会費会計を除外した有効な費目を返す"""
        qs = (
            Himoku.objects.exclude(accounting_class__accounting_name=settings.COMMUNITY_ACCOUNTING)
            .filter(alive=True)
            .distinct()
        )
        return qs

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

    requester = models.CharField(verbose_name="振込依頼人名", max_length=64, blank=True, null=True)
    himoku = models.ForeignKey(Himoku, verbose_name="費目名", on_delete=models.CASCADE, blank=True, null=True)
    comment = models.CharField(verbose_name="備考", max_length=64, blank=True, null=True)

    def __str__(self):
        if self.requester:
            return self.requester
        else:
            return ""

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

    account = models.ForeignKey(Account, verbose_name="口座名", on_delete=models.CASCADE, null=True)
    is_income = models.BooleanField(verbose_name="入金flg", default=False)
    transaction_date = models.DateField(verbose_name="取引日")
    amount = models.IntegerField(verbose_name="金額", default=0)
    himoku = models.ForeignKey(Himoku, verbose_name="費目名", on_delete=models.CASCADE, null=True)
    requesters_name = models.CharField(verbose_name="振込依頼人名", max_length=64, default="")
    description = models.CharField(verbose_name="摘要", max_length=64, default="")
    balance = models.IntegerField(verbose_name="残高", null=True, blank=True)
    author = models.ForeignKey(user, verbose_name="記録者", on_delete=models.CASCADE, null=True)
    created_date = models.DateTimeField(verbose_name="作成日", default=timezone.now)
    delete_flg = models.BooleanField(default=False)
    calc_flg = models.BooleanField(default=True)
    # 2023-08-20 前受金を分別するための手入力データフラグ。
    # 合算入力された取引データの相殺データと、分割して追加入力したデータではTrueにする。
    is_manualinput = models.BooleanField(default=False)
    # 2023-12-19支払い承認フラグを追加。
    is_approval = models.BooleanField(verbose_name="承認必要", default=True)
    # 請求金額合計内訳データとの比較用に追加(2024-09-04)
    is_billing = models.BooleanField(verbose_name="請求項目", default=True)
    # 前払い金フラグを追加。当月の月次収入チェックでは合計に含めない（2024-11-19）
    is_maeukekin = models.BooleanField(verbose_name="前受金", default=False)
    # 未収金振込フラグを追加。月次収入チェックでは合計に含めない（2024-11-22）
    # 未収金振込フラグは使用禁止とした。（2025-01-22）
    is_mishuukin = models.BooleanField(verbose_name="未収金", default=False)
    # 「前期の未払い分」フラグを追加。（2025-01-18）
    is_miharai = models.BooleanField(verbose_name="未払金支払い", default=False)

    def __str__(self):
        if self.himoku:
            return self.himoku.himoku_name
        return ""

    @staticmethod
    def get_maeuke(year, month):
        """通帳データの前受金(is_maeukekinフラグがon)合計を返す
        他の関数（stattic method）に依存するため、インスタンス関数とする。
        """
        tstart, tend = select_period(year, month)
        total = 0
        qs = Transaction.objects.filter(transaction_date__range=[tstart, tend]).filter(is_maeukekin=True)
        for i in qs:
            total += i.amount
        return total

    @staticmethod
    def total_all(sql):
        """calc_flgがONの合計金額を返す"""
        total_deposit = 0
        total_withdrawals = 0
        for data in sql:
            # 収入項目で前受金でない場合、収入合計計算する。月次収入チェック用。
            if data.is_income:
                total_deposit += data.amount
            # 収入項目で
            else:
                total_withdrawals += data.amount
        return total_deposit, total_withdrawals

    @staticmethod
    def total_with_calc_flg(sql):
        """calc_flgがONの合計金額を返す"""
        total_deposit = 0
        total_withdrawals = 0
        for data in sql:
            if data.calc_flg:
                # 収入項目で前受金でない場合、収入合計計算する。月次収入チェック用。
                if data.is_income:
                    total_deposit += data.amount
                # 収入項目で
                else:
                    total_withdrawals += data.amount
        return total_deposit, total_withdrawals

    @staticmethod
    def total_without_calc_flg(sql):
        """calc_flgがONの合計金額を返す
        - 収入の場合は前受金を除外した通帳データの合計を返す
        - 支出の場合はcalc_flgがONの支出合計を返す
        """
        total_deposit = 0
        total_withdrawals = 0
        for data in sql:
            if data.calc_flg:
                # 収入項目で前受金でない場合、収入合計計算する。月次収入チェック用。
                if data.is_income and not data.is_maeukekin:
                    total_deposit += data.amount
                # 収入項目で
                else:
                    total_withdrawals += data.amount
        return total_deposit, total_withdrawals

    @classmethod
    def get_qs_pb(cls, tstart, tend, account, ac_class, deposit_flg, manualinput, calc_flg):
        """資金移動を除外した入出金データquerysetを返す。
        - tstart/tend : 抽出期間。
        - account:口座名（Kuraselの場合は1口座となる。
        - ac_class:会計区分。
        - deposit_flg:入金はincome、出金はexpense。""の場合は入出金の両方を抽出する。
        - manualinput:手入力データを含めて抽出の場合はTrue。
        - manualinput:Trueの場合は補正データを含めて表示する。Falseの場合はKuraselの入出金明細データだけを抽出。
        - calc_flg:Falseの場合calc_flgを無視する。Trueの場合はcalc_flgがONのデータだけを抽出。
            - すまい・る債、共用保険料の資産振替の場合にcalc_flgはOFFとしている。
        """
        qs_pb = cls.objects.all().select_related("himoku")
        # 補正データを含める場合は手入力filterをしない。
        if manualinput:
            qs_pb = qs_pb.filter(transaction_date__range=[tstart, tend])
        else:
            qs_pb = qs_pb.filter(transaction_date__range=[tstart, tend]).filter(is_manualinput=False)
        # 入金・出金のfilter
        if deposit_flg == "income":
            qs_pb = qs_pb.filter(is_income=True)
        elif deposit_flg == "expense":
            qs_pb = qs_pb.filter(is_income=False)
        # 口座種類でfilter（Kuraselでは1口座なので常にacoountは""とする。
        if account != "0":
            qs_pb = qs_pb.filter(account=account)
        # 費目の会計区分でfilter
        if ac_class != "0":
            qs_pb = qs_pb.filter(himoku__accounting_class=ac_class)
        # calc_flgがFalseの場合、資金移動（すまい・る債、共用保険料等）を除外する
        if calc_flg:
            qs_pb = qs_pb.filter(calc_flg=calc_flg)
        return qs_pb

    @classmethod
    def dwd_from_kurasel(
        cls,
        data,
        paymentmethod_list,
        requester_list,
        default_himoku,
        banking_fee_himoku,
    ):
        """kurasel_translatorからDeposits and withdrawals（入出金明細データ）を読み込む
        - 戻り値：取り込んだ「月」(int型)。エラーの場合は0を返す。
        - 種類、日付、金額、振り込み依頼人でget_or_createする。
        - 口座は管理会計に決め打ち(id=3)。
        - 費目はdefaultの費目オブジェクト。
        - 勘定科目・費目は手入力となる。
        """
        data_list = data["data_list"]
        # 記録者
        author_obj = user.objects.get(id=data["author"])
        # error flag
        error_list = []
        # rtnのデフォルト値（最初のデータの「月」）
        rtn = data_list[0][1].month
        # 取り込んだデータの保存処理。
        for item in data_list:
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
                # (1)「振込依頼人」で費目を推定する。
                for requester in requester_list:
                    if item[4] == requester.requester:
                        himoku_obj = requester.himoku
                        himoku_chk = False
                        break
                # (2)「振込依頼人」で推定できない場合「支払い方法」で費目を推定する。
                if himoku_chk:
                    for paymentmethod in paymentmethod_list:
                        if item[5] == paymentmethod.account_description:
                            himoku_obj = paymentmethod.himoku_name
                            break
                # (3) 最後に「摘要欄」で費目を推定する。ToDo アドホック対応のため見直すこと。
                if himoku_chk:
                    if item[5] in ("892トリアツカイリヨウ", "893フリコミテスウリヨウ"):
                        himoku_obj = banking_fee_himoku

            # 保存処理（日付、金額、振込依頼人名が一致する場合、上書き保存しない）
            try:
                cls.objects.get_or_create(
                    transaction_date=item[1],
                    amount=item[2],
                    requesters_name=item[4],
                    defaults={
                        "account": Account.objects.all().first(),
                        "is_income": income,
                        "transaction_date": item[1],
                        "himoku": himoku_obj,
                        "amount": int(item[2]),
                        "balance": item[3],
                        "requesters_name": item[4],
                        "description": item[5],
                        "author": author_obj,
                    },
                )
            except Exception as e:
                logger.error(e)
                error_list.append(item[4])
                rtn = 0
        return rtn, error_list

    @classmethod
    def set_is_approval_text(cls, qs_transaction):
        """摘要欄文字列で支払い承認が必要かどうかのフラグを設定する
        - ToDo 今の所「費目」で支払い承認不要としていてもチェックをする。
        """
        qs_check = ApprovalCheckData.objects.filter(alive=True)
        if not qs_check:
            return None

        updated_objs = []  # 更新対象を貯めるリスト

        for transaction_obj in qs_transaction:
            description = transaction_obj.description
            if not description:
                continue

            # 承認不要条件に合致するかチェック
            is_match = False
            for chk_text in qs_check:
                # str()でラップして警告を回避
                if re.search(str(chk_text.atext), str(description)):
                    is_match = True
                    break

            # 条件に合致し、かつ現在の値がTrue（承認必要）なら変更
            if is_match and transaction_obj.is_approval:
                transaction_obj.is_approval = False
                updated_objs.append(transaction_obj)

        # 最後にまとめて一括更新（1回のSQLで済む）
        # 第一引数には更新対象のobjectのリスト、fieldsには更新したいカラムを指定する。
        # この時、fieldsに設定しないカラムは更新されない。
        if updated_objs:
            cls.objects.bulk_update(updated_objs, ["is_approval"])

        return None

    @classmethod
    def set_is_approval_himoku(cls, qs_transaction):
        """費目で支払い承認が必要かどうかのフラグを設定する
        - ToDo 今の所「費目」で支払い承認不要としていてもチェックをする。
        """
        # 入出金明細データでループ
        for qs_data in qs_transaction:
            is_approval = qs_data.himoku.is_approval
            if is_approval is False:
                pk = qs_data.id
                obj = cls.objects.get(pk=pk)
                obj.is_approval = False
                obj.save()
        return None

    @classmethod
    def get_year_income(cls, tstart, tend, manualinput):
        """入出金明細（通帳）の年間収入リストを返す。
        - 町内会費は含む。
        - tstart/tend : 抽出期間。
        - manualinput:Trueの場合は補正データを含めて表示する。Falseの場合はKuraselの入出金明細データだけを表示。
        - 費目レベルで集計フラグがON
        - 収入データレベルで集計フラグがON
        """
        qs_pb = cls.objects.values("himoku__himoku_name").annotate(price=Sum("amount"))
        # 入金のfilter
        qs_pb = qs_pb.filter(is_income=True)
        # 補正データを含める場合はfilterをしない。
        if manualinput:
            qs_pb = qs_pb.filter(transaction_date__range=[tstart, tend])
        else:
            qs_pb = qs_pb.filter(transaction_date__range=[tstart, tend]).filter(is_manualinput=False)
        # 計算フラグでfilterする
        qs_pb = qs_pb.filter(calc_flg=True)
        qs_pb = qs_pb.filter(himoku__aggregate_flag=True)
        return qs_pb

    @classmethod
    def get_year_expense(cls, tstart, tend):
        """費目名で集計した出金リストのquerysetをDictで返す。
        - tstart/tend : 抽出期間。
        - 資金移動は除外する。
        - 前期の未払いの支払いは除外する。
        - 非有効の費目データは除外する。
        """
        qs_pb = cls.objects.values("himoku__himoku_name").annotate(price=Sum("amount"))
        # 出金だけを抽出
        qs_pb = qs_pb.filter(is_income=False)
        # 抽出期間。
        qs_pb = qs_pb.filter(transaction_date__range=[tstart, tend])
        # 資金移動（計算フラグOFF）を除外
        qs_pb = qs_pb.filter(calc_flg=True)
        # 前期の未払い分は除外
        qs_pb = qs_pb.filter(is_miharai=False)
        # ToDo 金額0は除外。この方法ではマイナスの支出も除外してしまう
        qs_pb = qs_pb.filter(price__gt=0)
        return qs_pb


class ApprovalCheckData(models.Model):
    """入出金明細データの「支払い承認」が必要か否かを判定するための文字列オブジェクト"""

    atext = models.CharField(verbose_name="チェック文字列", max_length=16, blank=True, null=True, unique=True)
    comment = models.CharField(verbose_name="備考", max_length=50, blank=True, null=True)
    alive = models.BooleanField(verbose_name="有効", default=True)

    def __str__(self):
        return self.atext


class ClaimData(models.Model):
    """管理費等請求一覧データ"""

    claim_date = models.DateField(verbose_name="取引日")
    claim_type = models.CharField(
        verbose_name="請求種別",
        choices=settings.CLAIMTYPE,
        max_length=4,
        default=settings.RECIVABLE,
    )
    room_no = models.CharField(verbose_name="部屋番号", max_length=16, default="")
    name = models.CharField(verbose_name="氏名", max_length=16, default="")
    amount = models.IntegerField(verbose_name="金額", default=0)
    comment = models.CharField(verbose_name="摘要", max_length=64, default="")

    def __str__(self):
        return self.claim_type

    @classmethod
    def claim_from_kurasel(cls, data):
        """管理費等請求一覧データを保存処理する
        - 取り込む前に同じ年月、同じ請求種別のデータを削除することで重複登録を防止する
        """
        # 支払日
        date_str = str(data["year"]) + str(data["month"]).zfill(2) + "01"
        claim_date = datetime.datetime.strptime(date_str, "%Y%m%d").date()
        claim_type = data["claim_type"]

        # 同じ年月・請求種別のデータを削除
        cls.objects.filter(claim_date=claim_date, claim_type=claim_type).delete()

        error_list = []
        rtn = True
        for item in data["data_list"]:
            try:
                cls.objects.create(
                    claim_date=claim_date,
                    claim_type=claim_type,
                    room_no=item[1],
                    name=item[2],
                    amount=item[3],
                )
            except Exception as e:
                logger.error(e)
                error_list.append(item[0])
                rtn = False
        return rtn, error_list

    @classmethod
    def get_maeuke_claim(cls, year, month):
        """指定された年月に使われる前受金dictのリストを返す"""
        date_str = str(year) + str(month).zfill(2) + "01"
        claim_date = datetime.datetime.strptime(date_str, "%Y%m%d")
        maeuke_dict = (
            cls.objects.filter(claim_date=claim_date)
            .filter(claim_type=settings.MAEUKE)
            .values("claim_date", "room_no", "amount", "comment")
        )
        # 前受金の合計
        total = 0
        comment = ""
        for i in maeuke_dict:
            total += i["amount"]
            comment += i["comment"]

        return total, maeuke_dict, comment

    @classmethod
    def get_mishuu(cls, year, month):
        """指定された年月の請求時未収金dictのリストを返す"""
        date_str = str(year) + str(month).zfill(2) + "01"
        claim_date = datetime.datetime.strptime(date_str, "%Y%m%d")
        mishuu_dict = (
            cls.objects.filter(claim_date=claim_date)
            .filter(claim_type=settings.RECIVABLE)
            .values("claim_date", "room_no", "amount")
        )
        # 未収金の合駅
        total = 0
        for i in mishuu_dict:
            total += i["amount"]

        return total, mishuu_dict

    @classmethod
    def get_claim_list(cls, tstart, tend, claim_type):
        """管理費等の請求時「未収金」「前受金」「請求不備」のリストを返す"""

        claim_qs = (
            cls.objects.filter(claim_date__range=[tstart, tend])
            .filter(claim_type=claim_type)
            .order_by("claim_date")
        )
        total = 0
        for i in claim_qs:
            total += i.amount

        return claim_qs, total
