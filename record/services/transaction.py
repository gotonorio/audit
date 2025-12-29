import logging

from django.db import transaction as db_transaction

from record.models import Account, Himoku, Transaction

logger = logging.getLogger(__name__)


def create_offset_transaction(*, base_transaction, user):
    """
    相殺用トランザクションを作成する
    - 引数に*を置くことでキーワード引数のみを受け付けるようにする。
    - 相殺処理は元データの金額のマイナスを登録する。
    """
    offset = Transaction(
        account=base_transaction.account,
        transaction_date=base_transaction.transaction_date,
        is_income=base_transaction.is_income,
        amount=base_transaction.amount * -1,
        requesters_name=base_transaction.requesters_name,
        description=f"{base_transaction.description}（相殺）",
        himoku=base_transaction.himoku,
        balance=base_transaction.balance,
        author=user,
        is_manualinput=True,
        calc_flg=True,
    )

    offset.save()

    logger.info(f"相殺作成: 元PK={base_transaction.pk} 新PK={offset.pk} by {user}")
    return offset


def create_divided_transactions(*, base_transaction, divide_forms, user):
    """
    分割トランザクションを作成する
    - *をつけることでキーワード引数のみを受け付けるようにする
    """
    base_amount = -base_transaction.amount

    # 分割したデータの合計金額をチェックする。
    total = sum(f.cleaned_data["amount"] for f in divide_forms if f.cleaned_data.get("amount"))

    if total != base_amount:
        raise ValueError(f"合計不一致: {total} != {base_amount}")

    # 分割したデータの費目はデフォルト費目とする
    default_himoku = Himoku.get_default_himoku()

    created = []

    with db_transaction.atomic():
        # formにはformsetがセットされているので、繰り返し処理する。
        for form in divide_forms:
            amount = form.cleaned_data.get("amount")
            if not amount or amount <= 0:
                continue

            tx = Transaction(
                # 講座は「管理会計口座」の1件だけ。
                account=Account.objects.first(),
                transaction_date=base_transaction.transaction_date,
                balance=base_transaction.balance,
                is_income=base_transaction.is_income,
                himoku=default_himoku,
                amount=amount,
                requesters_name=form.cleaned_data.get("requesters_name"),
                description=form.cleaned_data.get("description"),
                author=user,
                is_manualinput=True,
                calc_flg=True,
            )
            tx.save()
            created.append(tx)

            logger.info(f"分割作成: basePK={base_transaction.pk} amount={amount} by {user}")

    return created
