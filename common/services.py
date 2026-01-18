import calendar
import datetime

# common/services.py (または register/services.py)
import os
import shutil
from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.urls import reverse_lazy
from django.utils import timezone


def get_lastmonth(year, month):
    """前月を返す"""
    # 当月1日の値を出す
    thismonth = datetime.datetime(int(year), int(month), 1)
    # 前月末日の値を出す
    lastmonth = thismonth + datetime.timedelta(days=-1)

    return lastmonth.year, lastmonth.month


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


def check_period(year, month):
    """Kuraselの開始日をチェック"""
    # Kuraselによる会計処理は2023年4月以降。それ以前は表示しない。
    if int(year) < settings.START_KURASEL["year"] or (
        int(year) <= settings.START_KURASEL["year"] and int(month) < settings.START_KURASEL["month"]
    ):
        year = int(settings.START_KURASEL["year"])
        month = int(settings.START_KURASEL["month"])

    return year, month


def run_database_backup(user_name):
    """
    SQLite3データベースのバックアップを実行し、古いファイルを削除する。
    戻り値: (成功フラグ, メッセージ)
    """
    # 1. バックアップ元DBの確認
    db_path = Path(settings.DATABASES["default"]["NAME"])
    if db_path.suffix != ".sqlite3":
        return False, "バックアップはsqlite3形式のみ対応しています。"

    # 2. バックアップ先ディレクトリの準備
    # settings.BASE_DIR / "backupDB" のように設定から取得するのが安全です
    backup_dir = Path(settings.BASE_DIR) / "backupDB"
    backup_dir.mkdir(parents=True, exist_ok=True)  # ディレクトリがなければ作成

    # 3. バックアップファイル名の生成
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M")
    backup_filename = f"{timestamp}-({user_name})_{db_path.name}"
    target_path = backup_dir / backup_filename

    # 4. コピー実行
    try:
        shutil.copy2(db_path, target_path)  # copy2はメタデータ（更新日時など）も保持する
    except Exception as e:
        return False, f"コピー失敗: {str(e)}"

    # 5. 古いバックアップの削除 (ローテーション)
    try:
        # ディレクトリ内のファイルをリスト化し、作成日時順に並べる
        backup_files = sorted(list(backup_dir.glob(f"*_{db_path.name}")), key=os.path.getmtime)

        backup_limit = getattr(settings, "BACKUP_NUM", 20)
        while len(backup_files) > backup_limit:
            old_file = backup_files.pop(0)  # 一番古いファイルを取り出す
            old_file.unlink()  # 削除
    except Exception as e:
        # 削除失敗はログに残すが、バックアップ自体は成功したとみなす
        return True, f"バックアップ完了（古いファイルの削除に一部失敗: {str(e)}）"

    return True, f"DBをバックアップしました。ファイル名: {backup_filename}"
