from django.core.management.base import BaseCommand

from ...models import Process
from ...services.templates import sync_process_to_template


class Command(BaseCommand):
    help = "Sync all Process rows to their corresponding ProcessTemplate"

    def handle(self, *args, **options):
        count = 0
        for process in Process.objects.all().only("id"):
            sync_process_to_template(process.id)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Synced templates for {count} processes."))


