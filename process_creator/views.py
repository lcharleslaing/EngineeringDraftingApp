from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib.auth.decorators import login_required
from rbac.decorators import require_app_access
from django.db import models
from django.template.loader import render_to_string
from django.conf import settings
from .models import Process, Step, StepImage
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.conf import settings
from .models import Process, Step, StepImage
from xhtml2pdf import pisa
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os


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
def step_insert(request, pk: int, step_id: int, direction: str):
    process = get_object_or_404(Process, pk=pk)
    ref = get_object_or_404(Step, pk=step_id, process=process)
    title = request.POST.get("title", "New Step").strip() or "New Step"
    if direction not in ("up", "down"):
        return JsonResponse({"ok": False, "error": "Invalid direction"}, status=400)
    with transaction.atomic():
        insert_order = ref.order if direction == "up" else ref.order + 1
        # shift steps >= insert_order by +1
        Step.objects.filter(process=process, order__gte=insert_order).update(order=models.F('order') + 1)
        step = Step.objects.create(process=process, order=insert_order, title=title)
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


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def step_image_upload(request, pk: int, step_id: int):
    process = get_object_or_404(Process, pk=pk)
    step = get_object_or_404(Step, pk=step_id, process=process)
    # Expect an image file under 'image' or a pasted blob as 'file'
    file = request.FILES.get('image') or request.FILES.get('file')
    if not file:
        return JsonResponse({"ok": False, "error": "No image provided"}, status=400)
    max_order = step.images.aggregate(models.Max('order')).get('order__max') or 0
    img = StepImage.objects.create(step=step, image=file, order=max_order + 1)
    return JsonResponse({"ok": True, "id": img.id, "url": img.image.url, "order": img.order})


@login_required
@require_app_access('process_creator', action='delete')
@require_POST
def step_image_delete(request, pk: int, step_id: int, image_id: int):
    process = get_object_or_404(Process, pk=pk)
    step = get_object_or_404(Step, pk=step_id, process=process)
    img = get_object_or_404(StepImage, pk=image_id, step=step)
    img.delete()
    return JsonResponse({"ok": True})


@login_required
@require_app_access('process_creator', action='view')
def process_pdf(request, pk: int):
    process = get_object_or_404(Process, pk=pk)

    # Render the print template to HTML
    html_string = render_to_string('process_creator/print.html', {'process': process})

    # Helper to resolve static/media URLs for xhtml2pdf
    def link_callback(uri, rel):
        if uri.startswith('/media/'):
            path = os.path.join(settings.MEDIA_ROOT, uri.replace('/media/', ''))
            return path
        if uri.startswith('/static/'):
            # If STATIC_ROOT is set, prefer it; otherwise try finders
            static_root = getattr(settings, 'STATIC_ROOT', None)
            if static_root:
                return os.path.join(static_root, uri.replace('/static/', ''))
        return uri

    # Generate PDF via xhtml2pdf
    from io import BytesIO
    pdf_io = BytesIO()
    pisa.CreatePDF(src=html_string, dest=pdf_io, link_callback=link_callback, encoding='utf-8')
    pdf_io.seek(0)

    response = HttpResponse(pdf_io.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="process-{process.id}.pdf"'
    return response


@login_required
@require_app_access('process_creator', action='view')
def process_word(request, pk: int):
    process = get_object_or_404(Process, pk=pk)
    
    # Create a new Word document
    doc = Document()
    
    # Add title
    title = doc.add_heading(process.name, 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add description
    if process.description:
        doc.add_heading('Description', level=1)
        doc.add_paragraph(process.description)
    
    # Add steps
    if process.steps.exists():
        doc.add_heading('Steps', level=1)
        for step in process.steps.all():
            # Add step title
            step_heading = doc.add_heading(f'{step.order}. {step.title}', level=2)
            
            # Add step details
            if step.details:
                doc.add_paragraph(step.details)
            
            # Add step images
            if step.images.exists():
                for img in step.images.all():
                    try:
                        # Get the full path to the image
                        img_path = os.path.join(settings.MEDIA_ROOT, str(img.image))
                        if os.path.exists(img_path):
                            # Add image to document
                            paragraph = doc.add_paragraph()
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
                            run.add_picture(img_path, width=Inches(6))
                    except Exception as e:
                        # If image can't be added, just continue
                        pass
    
    # Add notes
    if process.notes:
        doc.add_heading('Notes', level=1)
        doc.add_paragraph(process.notes)
    
    # Save to BytesIO
    from io import BytesIO
    doc_io = BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    
    response = HttpResponse(doc_io.getvalue(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="process-{process.id}.docx"'
    return response

# Create your views here.
