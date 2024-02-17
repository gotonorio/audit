import logging

import markdown
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

logger = logging.getLogger(__name__)


@register.simple_tag
def url_replace(request, field, value):
    """GETパラメータを一部を置き換える.
    検索結果のpagenation処理用で、あまり使用する機会はない。
    https://qiita.com/okoppe8/items/54eb105c9c94c0960f14
    """
    url_dict = request.GET.copy()
    url_dict[field] = str(value)
    return url_dict.urlencode()


@register.filter
def subtract(value, arg):
    """引き算用フィルタ"""
    rtn = "None"
    str1 = str(value)
    str2 = str(arg)
    # if arg is not None and value is not None:
    # if str1.isnumeric() and str2.isnumeric():
    if str1 and str2:
        rtn = int(value) - int(arg)
    return rtn


@register.filter
def div(value, arg):
    """割り算用フィルタ"""
    if arg == 0:
        return ""
    return value / arg


@register.filter
def div_int(value, arg):
    """整数除算用フィルタ"""
    if arg == 0:
        return ""
    return value // arg


@register.filter
def multi(value, arg):
    """掛け算."""
    return int(value * arg)


@register.filter
def markdown_to_html(text):
    """マークダウンをhtmlに変換する。
    https://python-markdown.github.io/reference/#extensions
    このfilterでhtml表示する場合、bulmaではclass='content'が必要。
    """
    html = markdown.markdown(text, extensions=settings.MARKDOWN_EXTENSIONS)
    return mark_safe(html)
