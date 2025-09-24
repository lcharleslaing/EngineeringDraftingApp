from django.db import transaction
from django.utils import timezone
from typing import Optional

from ..models import Process, Step, ProcessTemplate, TemplateStep


@transaction.atomic
def sync_process_to_template(process_id: int) -> ProcessTemplate:
    """
    Upsert a ProcessTemplate from Process + Steps (order preserved).
    If template exists, bump version and replace TemplateSteps in a transaction.
    Copy over name, module, description, notes.
    """
    process = Process.objects.select_related("module").prefetch_related("steps").get(id=process_id)

    created = False
    try:
        template = ProcessTemplate.objects.select_for_update().get(source_process=process)
        template.version += 1
        template.name = process.name
        template.module = process.module
        template.description = (process.summary or '').strip() or (process.description or '')
        template.notes = process.notes
        template.is_active = True
        template.save()
    except ProcessTemplate.DoesNotExist:
        template = ProcessTemplate.objects.create(
            name=process.name,
            module=process.module,
            source_process=process,
            version=1,
            description=(process.summary or '').strip() or (process.description or ''),
            notes=process.notes,
            is_active=True,
        )
        created = True

    # Replace steps deterministically
    TemplateStep.objects.filter(template=template).delete()

    steps = list(process.steps.all().order_by("order", "id"))
    tpl_steps = [
        TemplateStep(
            template=template,
            order=step.order,
            title=step.title,
            details=step.details or "",
        )
        for step in steps
    ]
    if tpl_steps:
        TemplateStep.objects.bulk_create(tpl_steps)

    return template


