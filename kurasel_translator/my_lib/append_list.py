import calendar
import datetime
from urllib.parse import urlencode

from django.conf import settings
from django.urls import reverse_lazy
from django.utils import timezone


def normalize(tmp_list, add_row_num, value):
    """tmp_listの行数をadd_row_numだけ増やす。
    増やした要素はvalueで初期化する。
    リスト内包処理でリストを初期化。
    """
    col = len(tmp_list[0])
    for j in range(add_row_num):
        row = [value for i in range(col)]
        tmp_list.append(row)
    return tmp_list


def append_list(a_list, b_list, value):
    """a_listにb_listを列として追加する。"""
    cnt_a = len(a_list)
    cnt_b = len(b_list)
    # a_listとb_listの行数を揃える。
    if cnt_a > cnt_b:
        b_list = normalize(b_list, cnt_a - cnt_b, value)
    else:
        a_list = normalize(a_list, cnt_b - cnt_a, value)

    # a_listの各行にb_listを追加する。
    for i, row in enumerate(a_list):
        row.extend(b_list[i])

    return a_list


def list_to_dict(data_list):
    """ListからDictを作成する
    - [key1, value1, key2, value2,....]のリストから、
    - {'key1':'value1', 'key2':'value2',..... }の辞書を作成して返す。
    """
    bs_dict = {}
    for i in range(0, len(data_list), 2):
        key = data_list[i]
        value = data_list[i + 1]
        bs_dict[key] = value
    return bs_dict


def redirect_with_param(url_name, param_dict, encode_flg=False):
    """FormViewで取り込みに成功した場合の遷移urlを返す。
    - 呼び出し側では redirect(url) として利用する。
    - https://codelab.website/django-view-redirect-param/
    - https://codor.co.jp/django/how-to-use-render
    - encode_flgによってパラメータをエンコードする。
    """
    if encode_flg:
        redirect_url = reverse_lazy(url_name)
        parameters = urlencode(param_dict)
        url = f"{redirect_url}?{parameters}"
    else:
        url = reverse_lazy(url_name, kwargs=param_dict)
    return url


def get_period(year, month):
    """与えられた年月の範囲（月初、月末の日）を返す。
    - start_date:月初の日付は1日を返す。
    - end_date:翌月の1日を返す。
    - 受け取り側では __gte=start_date、__lt=end_dateでfilterする。
    """
    start_date = datetime.datetime(int(year), int(month), 1)
    if month == 12:
        end_date = datetime.datetime(int(year) + 1, 1, 1)
    else:
        end_date = datetime.datetime(int(year), int(month) + 1, 1)

    return start_date, end_date


def select_period(year, month):
    """検索期間を返す
    - start_date:月初の日付は1日を返す。
    - end_date:月末の日付を返す。
    - 受け取り側では __range=[start_date, end_date]でfilterする。
    - month=0の場合、年初から年末を返す。
    """
    # if str(month).isdecimal():
    if int(month) > 0:
        last_day = calendar.monthrange(int(year), int(month))[1]
        tstart = timezone.datetime(int(year), int(month), 1, 0, 0, 0)
        tend = timezone.datetime(int(year), int(month), last_day, 0, 0, 0)
    else:
        tstart = timezone.datetime(int(year), 1, 1, 0, 0, 0)
        tend = timezone.datetime(int(year), 12, 31, 0, 0, 0)
    return tstart, tend


def check_period(year, month):
    """Kuraselの開始日をチェック"""
    # Kuraselによる会計処理は2023年4月以降。それ以前は表示しない。
    if int(year) < settings.START_KURASEL["year"] or (
        int(year) <= settings.START_KURASEL["year"] and int(month) < settings.START_KURASEL["month"]
    ):
        year = int(settings.START_KURASEL["year"])
        month = int(settings.START_KURASEL["month"])

    return year, month
