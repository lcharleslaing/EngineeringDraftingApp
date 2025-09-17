from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib.auth.decorators import login_required
from rbac.decorators import require_app_access
from django.db import models
from .models import Process, Step


@login_required
@require_app_access('process_creator', action='view')
def process_list(request):
    processes = Process.objects.all()
    return render(request, "process_creator/list.html", {"processes": processes})


@login_required
@require_app_access('process_creator', action='edit')
def process_create(request):
    max_order = Process.objects.aggregate(models.Max("order")).get("order__max") or 0
    process = Process.objects.create(name="Untitled Process", order=max_order + 1)
    return redirect("process_creator:edit", pk=process.pk)


@login_required
@require_app_access('process_creator', action='edit')
def process_edit(request, pk: int):
    process = get_object_or_404(Process, pk=pk)
    return render(request, "process_creator/edit.html", {"process": process})


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def process_update(request, pk: int):
    process = get_object_or_404(Process, pk=pk)
    name = request.POST.get('name')
    description = request.POST.get('description')
    notes = request.POST.get('notes')
    if name is not None:
        if not name.strip():
            return JsonResponse({"ok": False, "error": "Name is required."}, status=400)
        process.name = name.strip()
    if description is not None:
        process.description = description
    if notes is not None:
        process.notes = notes
    process.save()
    return JsonResponse({"ok": True})


@login_required
@require_app_access('process_creator', action='delete')
def process_delete(request, pk: int):
    process = get_object_or_404(Process, pk=pk)
    process.delete()
    return redirect("process_creator:list")


@login_required
@require_app_access('process_creator', action='view')
def process_print(request, pk: int):
    process = get_object_or_404(Process, pk=pk)
    return render(request, "process_creator/print.html", {"process": process})


@login_required
@require_app_access('process_creator', action='view')
def process_copy_prompt(request, pk: int):
    process = get_object_or_404(Process, pk=pk)
    lines = [f"# {process.name}"]
    if process.description:
        lines.append(process.description)
    lines.append("\n## Steps")
    for step in process.steps.all():
        title = step.title.strip() or "(Untitled Step)"
        details = step.details.strip()
        if details:
            lines.append(f"{step.order}. {title} — {details}")
        else:
            lines.append(f"{step.order}. {title}")
    if process.notes:
        lines.append("\n## Notes")
        lines.append(process.notes)
    text = "\n\n".join(lines)
    return HttpResponse(text, content_type="text/markdown; charset=utf-8")


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def processes_reorder(request):
    order_list = request.POST.getlist("order[]")
    with transaction.atomic():
        for index, process_id in enumerate(order_list, start=1):
            Process.objects.filter(id=process_id).update(order=index)
    return JsonResponse({"ok": True})


@login_required
@require_app_access('process_creator', action='view')
def process_print_all(request):
    # ids parameter optional; if provided, filter
    ids = request.GET.getlist('ids')
    processes = Process.objects.all()
    if ids:
        processes = processes.filter(id__in=ids)
    return render(request, "process_creator/print_all.html", {"processes": processes})


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def steps_reorder(request, pk: int):
    process = get_object_or_404(Process, pk=pk)
    order_list = request.POST.getlist("order[]")
    with transaction.atomic():
        for index, step_id in enumerate(order_list, start=1):
            Step.objects.filter(process=process, id=step_id).update(order=index)
        Process.objects.filter(pk=process.pk).update()  # touch updated_at
    return JsonResponse({"ok": True})


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def step_add(request, pk: int):
    process = get_object_or_404(Process, pk=pk)
    max_order = process.steps.aggregate(models.Max("order")).get("order__max") or 0
    title = request.POST.get("title", "").strip()
    if not title:
        return JsonResponse({"ok": False, "error": "Title is required."}, status=400)
    step = Step.objects.create(
        process=process,
        order=max_order + 1,
        title=title,
        details=request.POST.get("details", ""),
    )
    return JsonResponse({"ok": True, "id": step.id, "order": step.order})


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def step_update(request, pk: int, step_id: int):
    process = get_object_or_404(Process, pk=pk)
    step = get_object_or_404(Step, pk=step_id, process=process)
    title = request.POST.get("title")
    details = request.POST.get("details")
    if title is not None:
        if not title.strip():
            return JsonResponse({"ok": False, "error": "Title is required."}, status=400)
        step.title = title.strip()
    if details is not None:
        step.details = details
    step.save()
    return JsonResponse({"ok": True})


@login_required
@require_app_access('process_creator', action='delete')
@require_POST
def step_delete(request, pk: int, step_id: int):
    process = get_object_or_404(Process, pk=pk)
    step = get_object_or_404(Step, pk=step_id, process=process)
    step.delete()
    for index, s in enumerate(process.steps.order_by("order", "id"), start=1):
        if s.order != index:
            Step.objects.filter(pk=s.pk).update(order=index)
    return JsonResponse({"ok": True})

# Create your views here.
