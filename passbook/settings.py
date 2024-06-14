"""
Django settings for passbook project.

Generated by 'django-admin startproject' using Django 3.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "register.apps.RegisterConfig",
    "record.apps.RecordConfig",
    "monthly_report.apps.MonthlyReportConfig",
    "check_record.apps.CheckRecordConfig",
    "control.apps.ControlConfig",
    "budget.apps.BudgetConfig",
    "payment.apps.PaymentConfig",
    "kurasel_translator.apps.KuraselTranslatorConfig",
    "explanation.apps.ExplanationConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "passbook.middleware.UAmiddleware",
]

ROOT_URLCONF = "passbook.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "passbook.context_processors.version_no",
                "passbook.context_processors.is_debug",
            ],
            "libraries": {
                "my_templatetags": "templatetags.my_extras",
            },
        },
    },
]

WSGI_APPLICATION = "passbook.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "pb_audit.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "ja"

TIME_ZONE = "Asia/Tokyo"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

##################################################################
# User settings
##################################################################
CSRF_TRUSTED_ORIGINS = ["https://passbook.sophiagardens.org"]
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
VERSION_NO = "2024-06-15"
# DBのバックアップ保持数
BACKUP_NUM = 20
# # 資金移動の費目名を設定
# SHIKIN_IDOU = '資金移動'

# 前受金の費目名を設定
MAEUKE = "前受金"
# 町内会費会計
COMMUNITY_ACCOUNTING = "町内会費会計"
# Kurasel監査のスタート年月
START_KURASEL = {"year": 2023, "month": 4}
# Kurasel監査のスタート前月の未払金額
MIHARAI_INITIAL = 12429350
# Kurasel監査のスタート前月の未収金額
MISHUU_KANRI = 49930
MISHUU_SHUUZEN = 57000
MISHUU_PARKING = 165560
# Kurasel監査のスタート前月の前受金
MAEUKE_INITIAL = 17000

# Kuraselデータ取り込み時のチェック用。無くてもエラーチェックしないだけのはず。
KANRI_INCOME = ["収入", "管理費会計", "管理費", "緑地維持管理費"]
KANRI_PAYMENT = ["支出", "管理費会計", "管理委託業務費", "管理手数料"]
SHUUZEN_INCOME = ["収入", "修繕積立金会計", "修繕積立金", "専用庭使用料"]
SHUUZEN_PAYMENT = ["支出", "修繕積立金会計", "計画修繕工事費", "消防設備更新費用"]
PARKING_INCOME = ["収入", "駐車場会計", "駐車料"]
PARKING_PAYMENT = ["支出", "駐車場会計", "機械式駐車機保守料", "機械式駐車機工事費"]
COMMUNITY_INCOME = ["収入", "町内会会計", "町内会費", "町内会費会計"]
COMMUNITY_PAYMENT = ["支出", "町内会会計", "町会費", "寄付金", "町内会費会計"]
# 相殺処理後のデータ入力個数
FORMSET_NUM = 10
MONTH_ALL = (
    (0, "ALL"),
    (1, "1月"),
    (2, "2月"),
    (3, "3月"),
    (4, "4月"),
    (5, "5月"),
    (6, "6月"),
    (7, "7月"),
    (8, "8月"),
    (9, "9月"),
    (10, "10月"),
    (11, "11月"),
    (12, "12月"),
)
MONTH = (
    (1, "1月"),
    (2, "2月"),
    (3, "3月"),
    (4, "4月"),
    (5, "5月"),
    (6, "6月"),
    (7, "7月"),
    (8, "8月"),
    (9, "9月"),
    (10, "10月"),
    (11, "11月"),
    (12, "12月"),
)
CLAIMTYPE = (
    ("未収金", "請求時点未収金一覧"),
    ("前受金", "請求時点前受金一覧"),
    ("振替不備", "口座振替不備分"),
)

# カスタムユーザモデルを使う。
AUTH_USER_MODEL = "register.User"
NUMBER_GROUPING = 3
LOGIN_URL = "register:login"
LOGIN_REDIRECT_URL = "register:mypage"
# ログアウト画面を表示する場合はコメントアウトする。
# リダイレクトするとHTTP302が返されるからログアウト画面を表示する。
# LOGOUT_REDIRECT_URL = "register:login"
# ブラウザを閉じたらログアウトさせる。
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# 支払い記録の費目を勘定科目マスタコード3（共用部直接費）でフィルターする
# APPROVAL_ACCOUNTTITLE = 3
# 旧コミュニティワンの月次収支報告は2ヶ月遅れ
DELAY_MONTH = 0
# 管理費の後納を抽出するたのフィルター用金額（この金額以上は通常収入とする）
INCOME_NORMAL_KANRIHI = 2000000
# markdown用
MARKDOWN_EXTENSIONS = [
    "markdown.extensions.extra",
    "markdown.extensions.codehilite",
]

# secret keyのセット。
try:
    from .private_settings import *
except ImportError:
    pass
# DEBUGモードのセット。
try:
    from .local_settings import *
except ImportError:
    pass

# ログ出力先のディレクトリを設定する
# https://docs.djangoproject.com/ja/4.0/topics/logging/
# https://qiita.com/okoppe8/items/3e8ab77c5801a7d21991
LOG_BASE_DIR = os.path.join(
    "logs",
)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {"simple": {"format": "%(asctime)s [%(levelname)s] %(message)s"}},
    # ログの出力方法についての設定。
    "handlers": {
        # DEBUG = Falseの場合、ログファイルに出力する。
        "info": {
            "level": "INFO",
            "filters": ["require_debug_false"],
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": 51200,
            "backupCount": 5,
            "filename": os.path.join(LOG_BASE_DIR, "info.log"),
            "formatter": "simple",
        },
        "warning": {
            "level": "WARNING",
            "filters": ["require_debug_false"],
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": 51200,
            "backupCount": 5,
            "filename": os.path.join(LOG_BASE_DIR, "warning.log"),
            "formatter": "simple",
        },
        # DEBUG = Trueの場合、コンソールにログ出力する。
        "debug": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    # ロガーはルートロガーのみとする。
    "root": {
        "handlers": ["info", "warning", "debug"],
        "level": "DEBUG",
    },
}

# For debugging
if DEBUG:
    # 開発環境における静的ファイルの場所を指定する。
    STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
    # for django-debug-toolbar
    INTERNAL_IPS = ["127.0.0.1"]
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.logging.LoggingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
    ]
else:
    # for nginx
    STATIC_ROOT = "/code/static"

#
# グループ権限(各グループは下位グループの権限も含むようにする)
#
# login(区分所有者グループで予算実績対比表のみ閲覧可能): view_expensebudget
# director(理事会、専門委員会グループ): view_transaction
# data_manager(データ登録権限グループ): add_transaction
# chairman(プログラム開発グループ): add_user
