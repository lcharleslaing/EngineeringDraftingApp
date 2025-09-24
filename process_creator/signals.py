from django.db.models.signals import post_save, post_delete
from django.db import transaction
from django.dispatch import receiver

from .models import Process, Step
from .services.templates import sync_process_to_template


def _queue_sync(process_id: int):
    # Delay until after transaction commits; guard if process was deleted as
    # part of a cascading operation (e.g., deleting the whole process)
    def _do():
        try:
            if Process.objects.filter(id=process_id).exists():
                sync_process_to_template(process_id)
        except Exception:
            # Swallow sync errors in signals to avoid breaking CRUD ops
            pass
    transaction.on_commit(_do)


@receiver(post_save, sender=Process)
def process_saved(sender, instance: Process, created, **kwargs):
    _queue_sync(instance.id)


@receiver(post_delete, sender=Step)
@receiver(post_save, sender=Step)
def step_changed(sender, instance: Step, **kwargs):
    _queue_sync(instance.process_id)


