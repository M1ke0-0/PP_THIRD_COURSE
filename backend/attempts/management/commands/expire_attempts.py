from django.core.management.base import BaseCommand

from attempts.services import expire_overdue_attempts


class Command(BaseCommand):
    help = 'Завершает со статусом EXPIRED попытки, у которых вышло время. Запускать по cron раз в минуту.'

    def handle(self, *args, **options):
        count = expire_overdue_attempts()
        self.stdout.write(self.style.SUCCESS(f'Завершено попыток: {count}'))
