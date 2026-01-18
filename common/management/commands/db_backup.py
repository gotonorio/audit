from common.services import run_database_backup
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "SQLite3データベースをバックアップします"

    def handle(self, *args, **options):
        # Cron実行なのでユーザー名は "system_cron" とします
        success, message = run_database_backup("system_cron")

        if success:
            self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stdout.write(self.style.ERROR(message))
