import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def check_copy_area(data_list):
    """コピーした範囲をチェック
    - エラーがある場合はエラーメッセージを返す
    - 正しければ、err_msg = Falseを返す
    """
    err_msg = False
    # (1) １行目は「収入の部」「支出の部」
    if data_list[0] not in ("収入の部", "支出の部"):
        err_msg = "ヘッダの「収入の部」または「支出の部」の行からコピーしてください"
        return err_msg
    # (2) 最下行に「合計」が含まれているか.
    for item in data_list:
        if item in ("合計",):
            err_msg = "「合計」の行は含めないでください"
            return err_msg
    return err_msg


def check_accountingclass(data_list, ac):
    """取り込んだ月次収支データのチェック
    - d[0] : 費目名
    - ac   : 会計区分
    """
    for d in data_list:
        if d[0] in settings.KANRI_INCOME and ac in settings.KANRI_INCOME:
            return True
        elif d[0] in settings.KANRI_PAYMENT and ac in settings.KANRI_PAYMENT:
            return True
        elif d[0] in settings.SHUUZEN_INCOME and ac in settings.SHUUZEN_INCOME:
            return True
        elif d[0] in settings.SHUUZEN_PAYMENT and ac in settings.SHUUZEN_PAYMENT:
            return True
        elif d[0] in settings.PARKING_INCOME and ac in settings.PARKING_INCOME:
            return True
        elif d[0] in settings.PARKING_PAYMENT and ac in settings.PARKING_PAYMENT:
            return True
        elif d[0] in settings.COMMUNITY_INCOME and ac in settings.COMMUNITY_INCOME:
            return True
        elif d[0] in settings.COMMUNITY_PAYMENT and ac in settings.COMMUNITY_PAYMENT:
            return True
    return False


def check_period(year, month):
    """Kuraselの開始日をチェック"""
    # Kuraselによる会計処理は2023年4月以降。それ以前は表示しない。
    if int(year) < settings.START_KURASEL["year"] or (
        int(year) <= settings.START_KURASEL["year"] and int(month) < settings.START_KURASEL["month"]
    ):
        year = int(settings.START_KURASEL["year"])
        month = int(settings.START_KURASEL["month"])

    return year, month


def check_data_kind(data_list):
    """ヘッダから「収入」「支出」を判断してからヘッダ部分を除去したdata_listを返す"""
    if data_list[0] in ("収入の部"):
        data_type = "収入"
    else:
        data_type = "支出"
    # 先頭から6要素を削除
    del data_list[0:6]
    return data_type, data_list
