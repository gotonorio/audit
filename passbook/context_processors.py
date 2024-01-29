from django.conf import settings


def version_no(request):
    """プロジェクト共通のTextをtemplatesファイルで使えるように"""
    return {"VERSION_NO": settings.VERSION_NO}


def is_debug(request):
    """DEBUGモードを判定する"""
    return {"DEBUG": settings.DEBUG}
