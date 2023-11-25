import logging

from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.dispatch import receiver
from django.utils import timezone

logger = logging.getLogger(__name__)


class User(AbstractUser):
    """デフォルトのユーザモデルを使う"""

    pass


@receiver(models.signals.post_save, sender=User)
def post_save_user_signal_handler(sender, instance, created, **kwargs):
    """シグナルによってUserにgroupを追加する。
    https://stackoverflow.com/questions/51974276/how-to-automatically-add-group-and-staff-permissions-when-user-is-created/51975193
    """
    if created:
        try:
            group = Group.objects.get(name="guest")
        except ObjectDoesNotExist:
            pass
        else:
            instance.groups.add(group)
            instance.save()


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    """ログインした際に呼ばれて、管理者ならログ記録する"""
    if user_is_manager(request, user):
        logger.info(f"{user} login")


@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    """ログアウトした際に呼ばれる"""
    if user_is_manager(request, user):
        logger.info(f"{user} logout")


def user_is_manager(request, user):
    """userが「管理者」どうかの判定(adminuserは除外)"""
    rtn = False
    qs = request.user.groups.values_list("name", flat=True)
    if qs and list(qs)[0] in ["chairman", "data_manager"]:
        rtn = True
    return rtn
