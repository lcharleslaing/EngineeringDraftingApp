from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib.auth.decorators import login_required
from rbac.decorators import require_app_access
from django.db import models
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import Module, Process, Step, StepImage, StepLink, StepFile, AIInteraction
from xhtml2pdf import pisa
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os
import json
import openai
import re
from decimal import Decimal
from io import BytesIO
from urllib.parse import quote
import subprocess
import tempfile


def markdown_to_plain_text(text):
    """Convert basic Markdown formatting to plain text with proper formatting"""
    if not text:
        return ""
    
    # Convert headers
    text = re.sub(r'^### (.+)$', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'\1', text, flags=re.MULTILINE)
    
    # Convert bold text
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    
    # Convert italic text
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    
    # Convert bullet points
    text = re.sub(r'^\* (.+)$', r'• \1', text, flags=re.MULTILINE)
    text = re.sub(r'^- (.+)$', r'• \1', text, flags=re.MULTILINE)
    
    # Convert numbered lists
    text = re.sub(r'^(\d+)\. (.+)$', r'\1. \2', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()


@login_required
@require_app_access('process_creator', action='view')
def process_list(request):
    # Get all modules for the dropdown
    modules = Module.objects.all()
    
    # Get selected module from request
    selected_module_id = request.GET.get('module')
    selected_module = None
    
    if selected_module_id:
        try:
            selected_module = Module.objects.get(id=selected_module_id)
            processes = Process.objects.filter(module=selected_module).order_by('order', 'name')
        except Module.DoesNotExist:
            processes = Process.objects.all().order_by('order', 'name')
    else:
        processes = Process.objects.all().order_by('order', 'name')
    
    return render(request, "process_creator/list.html", {
        "processes": processes,
        "modules": modules,
        "selected_module": selected_module
    })


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def module_create(request):
    """Create a new Module via AJAX."""
    data = json.loads(request.body or '{}') if request.headers.get('Content-Type','').startswith('application/json') else request.POST
    name = (data.get('name') or '').strip()
    description = (data.get('description') or '').strip()
    if not name:
        return JsonResponse({"ok": False, "error": "Name is required"}, status=400)
    # Prevent duplicates (case-insensitive)
    existing = Module.objects.filter(name__iexact=name).first()
    if existing:
        return JsonResponse({"ok": True, "id": existing.id, "name": existing.name})
    module = Module.objects.create(name=name, description=description)
    return JsonResponse({"ok": True, "id": module.id, "name": module.name})


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
    modules = Module.objects.all()
    return render(request, "process_creator/edit.html", {"process": process, "modules": modules})


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def process_update(request, pk: int):
    process = get_object_or_404(Process, pk=pk)
    name = request.POST.get('name')
    description = request.POST.get('description')
    notes = request.POST.get('notes')
    summary = request.POST.get('summary')
    summary_instructions = request.POST.get('summary_instructions')
    analysis = request.POST.get('analysis')
    analysis_instructions = request.POST.get('analysis_instructions')
    module_id = request.POST.get('module')
    
    if name is not None:
        if not name.strip():
            return JsonResponse({"ok": False, "error": "Name is required."}, status=400)
        process.name = name.strip()
    if description is not None:
        process.description = description
    if notes is not None:
        process.notes = notes
    if summary is not None:
        process.summary = summary
    if summary_instructions is not None:
        process.summary_instructions = summary_instructions
    if analysis is not None:
        process.analysis = analysis
    if analysis_instructions is not None:
        process.analysis_instructions = analysis_instructions
    if module_id is not None:
        if module_id == '':
            process.module = None
        else:
            try:
                process.module = Module.objects.get(id=module_id)
            except Module.DoesNotExist:
                pass  # Keep existing module if invalid ID provided
    
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
@require_app_access('process_creator', action='edit')
@require_POST
def step_link_add(request, pk: int, step_id: int):
    process = get_object_or_404(Process, pk=pk)
    step = get_object_or_404(Step, pk=step_id, process=process)
    data = json.loads(request.body or '{}') if request.headers.get('Content-Type','').startswith('application/json') else request.POST
    title = (data.get('title') or '').strip()
    url = (data.get('url') or '').strip()
    if not title or not url:
        return JsonResponse({"ok": False, "error": "Title and URL are required"}, status=400)
    max_order = step.links.aggregate(models.Max('order')).get('order__max') or 0
    link = StepLink.objects.create(step=step, title=title, url=url, order=max_order + 1)
    return JsonResponse({"ok": True, "id": link.id, "title": link.title, "url": link.url})


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def step_link_delete(request, pk: int, step_id: int, link_id: int):
    process = get_object_or_404(Process, pk=pk)
    step = get_object_or_404(Step, pk=step_id, process=process)
    link = get_object_or_404(StepLink, pk=link_id, step=step)
    link.delete()
    return JsonResponse({"ok": True})


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def step_file_upload(request, pk: int, step_id: int):
    try:
        process = get_object_or_404(Process, pk=pk)
        step = get_object_or_404(Step, pk=step_id, process=process)
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({"ok": False, "error": "No file uploaded"}, status=200)
        name_lower = file.name.lower()
        max_order = step.files.aggregate(models.Max('order')).get('order__max') or 0

        # Direct PDF: save as-is
        if (file.content_type == 'application/pdf' or name_lower.endswith('.pdf')):
            sf = StepFile.objects.create(step=step, file=file, order=max_order + 1)
            return JsonResponse({"ok": True, "id": sf.id, "url": sf.file.url, "name": os.path.basename(sf.file.name)})

        # DWG / IDW: try local conversion to PDF
        is_dwg = name_lower.endswith('.dwg')
        is_idw = name_lower.endswith('.idw')
        if not (is_dwg or is_idw):
            return JsonResponse({"ok": False, "error": "Only PDF, DWG or IDW files are supported"}, status=200)

        # Persist the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp_in:
            for chunk in file.chunks():
                tmp_in.write(chunk)
            tmp_in_path = tmp_in.name

        tmp_out_fd, tmp_out_path = tempfile.mkstemp(suffix='.pdf')
        os.close(tmp_out_fd)

        if is_dwg:
            exe = getattr(settings, 'ODA_CONVERTER_PDF', '')
            if not exe or not os.path.exists(exe):
                # Fallback: store the DWG as-is so it can be linked/downloaded
                sf = StepFile.objects.create(step=step, file=file, order=max_order + 1)
                return JsonResponse({"ok": True, "id": sf.id, "url": sf.file.url, "name": os.path.basename(sf.file.name)})
            cmd = [exe, tmp_in_path, tmp_out_path]
        else:
            exe = getattr(settings, 'INVENTOR_IDW_TO_PDF', '')
            if not exe or not os.path.exists(exe):
                sf = StepFile.objects.create(step=step, file=file, order=max_order + 1)
                return JsonResponse({"ok": True, "id": sf.id, "url": sf.file.url, "name": os.path.basename(sf.file.name)})
            cmd = [exe, tmp_in_path, tmp_out_path]

        completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, timeout=120)
        if completed.returncode != 0 or not os.path.exists(tmp_out_path) or os.path.getsize(tmp_out_path) == 0:
            # On conversion failure, store original so user still gets a downloadable file
            try:
                os.unlink(tmp_out_path)
            except Exception:
                pass
            sf = StepFile.objects.create(step=step, file=file, order=max_order + 1)
            return JsonResponse({"ok": True, "id": sf.id, "url": sf.file.url, "name": os.path.basename(sf.file.name)})

        with open(tmp_out_path, 'rb') as f_out:
            from django.core.files.base import ContentFile
            pdf_bytes = f_out.read()
            pdf_name = os.path.splitext(file.name)[0] + '.pdf'
            sf = StepFile.objects.create(step=step, order=max_order + 1)
            sf.file.save(pdf_name, ContentFile(pdf_bytes), save=True)

        return JsonResponse({"ok": True, "id": sf.id, "url": sf.file.url, "name": os.path.basename(sf.file.name)})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=200)
    finally:
        try:
            if 'tmp_in_path' in locals() and os.path.exists(tmp_in_path):
                os.unlink(tmp_in_path)
        except Exception:
            pass
        try:
            if 'tmp_out_path' in locals() and os.path.exists(tmp_out_path):
                os.unlink(tmp_out_path)
        except Exception:
            pass


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def step_file_delete(request, pk: int, step_id: int, file_id: int):
    process = get_object_or_404(Process, pk=pk)
    step = get_object_or_404(Step, pk=step_id, process=process)
    sf = get_object_or_404(StepFile, pk=file_id, step=step)
    sf.delete()
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

    # Generate filename with process title and timestamp
    from datetime import datetime
    from urllib.parse import quote
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_title = "".join(c for c in process.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '-')
    filename = f"Process-{safe_title}-{timestamp}.pdf"
    
    response = HttpResponse(pdf_io.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{quote(filename)}"'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
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
    
    # Add summary
    if process.summary:
        doc.add_heading('Summary', level=1)
        # Format the summary text properly
        formatted_summary = markdown_to_plain_text(process.summary)
        # Split into paragraphs and add each one
        for paragraph in formatted_summary.split('\n\n'):
            if paragraph.strip():
                p = doc.add_paragraph(paragraph.strip())
                p.paragraph_format.space_after = Inches(0.1)
                p.paragraph_format.line_spacing = 1.15
    
    # Add description
    if process.description:
        doc.add_heading('Description', level=1)
        p = doc.add_paragraph(process.description)
        p.paragraph_format.space_after = Inches(0.1)
        p.paragraph_format.line_spacing = 1.15
    
    # Add steps
    if process.steps.exists():
        doc.add_heading('Steps', level=1)
        for step in process.steps.all():
            # Add step title
            step_heading = doc.add_heading(f'{step.order}. {step.title}', level=2)
            
            # Add step details
            if step.details:
                p = doc.add_paragraph(step.details)
                p.paragraph_format.space_after = Inches(0.1)
                p.paragraph_format.line_spacing = 1.15
            
            # Add step images
            if step.images.exists():
                for img in step.images.all():
                    try:
                        # Get the full path to the image
                        img_path = os.path.join(settings.MEDIA_ROOT, str(img.image))
                        if os.path.exists(img_path):
                            # Add image to document with border using table
                            table = doc.add_table(rows=1, cols=1)
                            table.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            cell = table.cell(0, 0)
                            cell.vertical_alignment = WD_ALIGN_PARAGRAPH.CENTER
                            
                            # Add image to cell
                            paragraph = cell.paragraphs[0]
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            run = paragraph.add_run()
                            run.add_picture(img_path, width=Inches(6))
                            
                            # Add border to table cell
                            from docx.oxml.shared import OxmlElement, qn
                            tc = cell._tc
                            tcPr = tc.get_or_add_tcPr()
                            tcBorders = OxmlElement('w:tcBorders')
                            for border_name in ['top', 'left', 'bottom', 'right']:
                                border = OxmlElement(f'w:{border_name}')
                                border.set(qn('w:val'), 'single')
                                border.set(qn('w:sz'), '12')  # 3pt border
                                border.set(qn('w:space'), '0')
                                border.set(qn('w:color'), '333333')
                                tcBorders.append(border)
                            tcPr.append(tcBorders)
                            
                    except Exception as e:
                        # If image can't be added, just continue
                        pass
    
    # Add notes
    if process.notes:
        doc.add_heading('Notes', level=1)
        p = doc.add_paragraph(process.notes)
        p.paragraph_format.space_after = Inches(0.1)
        p.paragraph_format.line_spacing = 1.15
    
    # Add analysis
    if process.analysis:
        doc.add_heading('Process Analysis', level=1)
        # Format the analysis text properly
        formatted_analysis = markdown_to_plain_text(process.analysis)
        # Split into paragraphs and add each one
        for paragraph in formatted_analysis.split('\n\n'):
            if paragraph.strip():
                p = doc.add_paragraph(paragraph.strip())
                p.paragraph_format.space_after = Inches(0.1)
                p.paragraph_format.line_spacing = 1.15
    
    # Save to BytesIO
    from io import BytesIO
    doc_io = BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    
    # Generate filename with process title and timestamp
    from datetime import datetime
    from urllib.parse import quote
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_title = "".join(c for c in process.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '-')
    filename = f"Process-{safe_title}-{timestamp}.docx"
    
    response = HttpResponse(doc_io.getvalue(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="{quote(filename)}"'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
@require_app_access('process_creator', action='view')
def process_stats(request, pk: int):
    process = get_object_or_404(Process, pk=pk)
    
    # Calculate statistics
    step_count = process.steps.count()
    
    # Count substeps (lines starting with -)
    substep_count = 0
    for step in process.steps.all():
        if step.details:
            # Count lines that start with - (substeps)
            substep_count += len([line for line in step.details.split('\n') if line.strip().startswith('-')])
    
    total_steps = step_count + substep_count
    image_count = sum(step.images.count() for step in process.steps.all())
    description_length = len(process.description) if process.description else 0
    notes_length = len(process.notes) if process.notes else 0
    
    # Format dates
    from django.utils import timezone
    created_at = process.created_at.strftime('%B %d, %Y at %I:%M %p')
    updated_at = process.updated_at.strftime('%B %d, %Y at %I:%M %p')
    
    stats = {
        'created_at': created_at,
        'updated_at': updated_at,
        'step_count': step_count,
        'substep_count': substep_count,
        'total_steps': total_steps,
        'image_count': image_count,
        'description_length': description_length,
        'notes_length': notes_length,
    }
    
    return JsonResponse(stats)


def call_openai_api(prompt, model="gpt-4o-mini", max_tokens=2000):
    """Helper function to call OpenAI API and track usage"""
    try:
        if not settings.OPENAI_API_KEY:
            return {
                'success': False,
                'error': 'OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.',
                'tokens_used': 0,
                'cost': Decimal('0.00')
            }
        
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        return {
            'success': True,
            'content': response.choices[0].message.content,
            'tokens_used': response.usage.total_tokens,
            'cost': calculate_cost(response.usage.total_tokens, model)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'tokens_used': 0,
            'cost': Decimal('0.00')
        }


def calculate_cost(tokens, model):
    """Calculate cost based on token usage and model"""
    # Pricing per 1K tokens (as of 2024)
    pricing = {
        'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
        'gpt-4o': {'input': 0.005, 'output': 0.015},
        'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002}
    }
    
    if model not in pricing:
        model = 'gpt-4o-mini'
    
    # Rough estimate - assume 50/50 input/output split
    cost_per_token = (pricing[model]['input'] + pricing[model]['output']) / 2
    return Decimal(str(tokens * cost_per_token / 1000)).quantize(Decimal('0.000001'))


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def ai_generate_summary(request, pk: int):
    """Generate AI summary for a process"""
    process = get_object_or_404(Process, pk=pk)
    
    # Debug: Check if API key is available
    if not settings.OPENAI_API_KEY:
        return JsonResponse({
            'success': False, 
            'error': 'OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.'
        })
    
    # Get custom instructions or use default
    data = json.loads(request.body)
    instructions = data.get('instructions', process.summary_instructions)
    
    # Build prompt with process data
    prompt = f"""{instructions}

Process Details:
Name: {process.name}
Description: {process.description or 'No description provided'}

Steps:
"""
    
    for step in process.steps.all():
        prompt += f"{step.order}. {step.title}\n"
        if step.details:
            prompt += f"   Details: {step.details}\n"
        if step.images.exists():
            prompt += f"   Images: {step.images.count()} screenshot(s)\n"
        prompt += "\n"
    
    if process.notes:
        prompt += f"Notes: {process.notes}\n"
    
    # Call OpenAI API
    result = call_openai_api(prompt, max_tokens=500)
    
    if result['success']:
        # Update process
        process.summary = result['content']
        process.summary_instructions = instructions
        process.last_ai_update = timezone.now()
        process.save()
        
        # Log interaction
        AIInteraction.objects.create(
            process=process,
            interaction_type='summary',
            prompt_sent=prompt,
            response_received=result['content'],
            tokens_used=result['tokens_used'],
            cost=result['cost']
        )
        
        return JsonResponse({
            'success': True,
            'summary': result['content']
        })
    else:
        return JsonResponse({
            'success': False,
            'error': result['error']
        })


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def ai_analyze_process(request, pk: int):
    """Generate AI analysis for process improvement"""
    process = get_object_or_404(Process, pk=pk)
    
    # Debug: Check if API key is available
    if not settings.OPENAI_API_KEY:
        return JsonResponse({
            'success': False, 
            'error': 'OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.'
        })
    
    # Get custom instructions or use default
    data = json.loads(request.body)
    instructions = data.get('instructions', process.analysis_instructions)
    
    # Build comprehensive prompt
    prompt = f"""You are a business process improvement consultant. {instructions}

Process Details:
Name: {process.name}
Description: {process.description or 'No description provided'}

Current Process Steps:
"""
    
    for step in process.steps.all():
        prompt += f"{step.order}. {step.title}\n"
        if step.details:
            prompt += f"   Details: {step.details}\n"
        if step.images.exists():
            prompt += f"   Images: {step.images.count()} screenshot(s)\n"
        prompt += "\n"
    
    if process.notes:
        prompt += f"Additional Notes: {process.notes}\n"
    
    prompt += f"\nCurrent Summary: {process.summary or 'No summary available'}\n"
    
    prompt += """
Please provide a detailed analysis following the instructions above. Structure your response with clear headings and actionable recommendations.
"""
    
    # Call OpenAI API
    result = call_openai_api(prompt, max_tokens=2000)
    
    if result['success']:
        # Update process
        process.analysis = result['content']
        process.analysis_instructions = instructions
        process.last_ai_update = timezone.now()
        process.save()
        
        # Log interaction
        AIInteraction.objects.create(
            process=process,
            interaction_type='analysis',
            prompt_sent=prompt,
            response_received=result['content'],
            tokens_used=result['tokens_used'],
            cost=result['cost']
        )
        
        return JsonResponse({
            'success': True,
            'analysis': result['content']
        })
    else:
        return JsonResponse({
            'success': False,
            'error': result['error']
        })

# Bulk Operations
@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def bulk_summary(request):
    """Generate summary for multiple processes"""
    try:
        data = json.loads(request.body)
        process_ids = data.get('process_ids', [])
        
        if not process_ids:
            return JsonResponse({'success': False, 'error': 'No processes selected'})
        
        # Get all selected processes
        processes = Process.objects.filter(id__in=process_ids).order_by('order')
        if not processes.exists():
            return JsonResponse({'success': False, 'error': 'No valid processes found'})
        
        # Combine all process data
        combined_data = []
        for process in processes:
            process_info = {
                'name': process.name,
                'description': process.description,
                'steps': []
            }
            
            for step in process.steps.all().order_by('order'):
                step_info = {
                    'title': step.title,
                    'details': step.details
                }
                process_info['steps'].append(step_info)
            
            combined_data.append(process_info)
        
        # Use the default summary instructions
        summary_instructions = "You are given a list of steps, bullet points, or fragmented notes. Your task is to transform them into a single professional, coherent paragraph. Do not repeat the steps as a list. Instead, weave them into smooth, natural prose that reads as if written by a skilled professional writer. Maintain accuracy, logical flow, and clarity. The output must always be a polished paragraph summary, never a bullet list."
        
        # Create comprehensive prompt
        prompt = f"{summary_instructions}\n\nProcess Data:\n{json.dumps(combined_data, indent=2)}"
        
        # Call OpenAI API
        result = call_openai_api(prompt, model='gpt-4o-mini')
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'summary': result['content']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error generating bulk summary: {str(e)}'
        })


@login_required
@require_app_access('process_creator', action='edit')
@require_POST
def bulk_analyze(request):
    """Generate analysis for multiple processes"""
    try:
        data = json.loads(request.body)
        process_ids = data.get('process_ids', [])
        
        if not process_ids:
            return JsonResponse({'success': False, 'error': 'No processes selected'})
        
        # Get all selected processes
        processes = Process.objects.filter(id__in=process_ids).order_by('order')
        if not processes.exists():
            return JsonResponse({'success': False, 'error': 'No valid processes found'})
        
        # Combine all process data
        combined_data = []
        for process in processes:
            process_info = {
                'name': process.name,
                'description': process.description,
                'notes': process.notes,
                'steps': []
            }
            
            for step in process.steps.all().order_by('order'):
                step_info = {
                    'title': step.title,
                    'details': step.details
                }
                process_info['steps'].append(step_info)
            
            combined_data.append(process_info)
        
        # Use the default analysis instructions
        analysis_instructions = """You are a senior operations analyst. You will receive a business process as input (steps, notes, and context). Produce a professional report titled "Training Analysis" that managers and frontline staff can act on.
Follow these rules:
- Write clearly and concisely; avoid jargon. Use confident, direct language.
- Do NOT restate the steps as bullets. Summarize the process in flowing prose.
- Use Markdown headings exactly as specified below.
- Give specific, actionable recommendations with clear benefits and effort levels.
- Where details are missing, make reasonable assumptions and state them briefly.
=== INPUT START ===
{PASTE PROCESS STEPS / NOTES / CONTEXT HERE}
=== INPUT END ===
=== OUTPUT FORMAT (Markdown) ===
# Training Analysis
## Executive Summary
A 4–6 sentence overview of the process, the primary objective, the current state, and the most important recommended changes and expected benefits.
## Process Narrative (Plain-Language Summary)
6–10 sentences that narrate how the process works from start to finish. Use paragraph form only (no bullets). Emphasize flow, handoffs, tools used, approvals, and timing.
## Assumptions
- 2–5 short bullets listing key assumptions you made due to missing information.
## Strengths
- 4–8 bullets. Each bullet: what works well + why it matters (impact on quality, speed, cost, compliance, safety, or CX).
## Weaknesses
- 4–8 bullets. Each bullet: the issue + consequence (e.g., rework, delays, risk, cost).
## Improvement Opportunities — Current System (No new software)
Provide 5–10 specific, low-friction changes using existing tools, roles, and policies. For each item, use this format in one bullet:
- **[Title]** — What to change (1–2 sentences). **Benefit:** expected outcome with a measurable indicator (e.g., "reduce cycle time by ~15%"). **Effort:** Low/Med/High. **Owner:** role. **Risk/Mitigation:** brief.
## Immediate Application-Level Enhancements (Quick to implement in an app/workflow)
Provide 3–7 changes that can be implemented quickly via simple configuration, scripts, forms, validations, templates, or notifications. For each item, use the same format:
- **[Title]** — What to implement (1–2 sentences). **Benefit:** measurable. **Effort:** Low/Med/High. **Owner:** role. **Risk/Mitigation:** brief.
## Implementation Roadmap
Organize recommendations into phases with rationale:
- **Now (0–30 days):** 3–6 highest-ROI, low-effort actions.
- **Next (30–90 days):** 3–6 medium-effort actions that compound earlier gains.
- **Later (90+ days):** 2–4 higher-effort changes that deliver strategic value.
## Metrics & Monitoring
List 4–8 KPIs with target direction and cadence. For each KPI: **Name**, **Target/Direction**, **Data Source**, **Review Cadence** (e.g., weekly), **Owner**.
## Risks & Mitigations
3–6 material risks across people/process/tech/compliance and how to mitigate each.
## Final Recommendation
A 4–6 sentence closing paragraph summarizing the case for change, expected benefits, and the immediate next steps.
=== STYLE GUARDRAILS ===
- Professional tone. Tight sentences. No filler, no hype.
- Use paragraph form for the narrative sections; bullets only where specified.
- Quantify benefits or ranges when plausible. Avoid vague claims.
- Do not include meta-commentary or instructions in the output."""
        
        # Create comprehensive prompt
        prompt = f"{analysis_instructions}\n\nProcess Data:\n{json.dumps(combined_data, indent=2)}"
        
        # Call OpenAI API
        result = call_openai_api(prompt, model='gpt-4o-mini')
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'analysis': result['content']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error generating bulk analysis: {str(e)}'
        })


@login_required
@require_app_access('process_creator', action='view')
def bulk_pdf(request):
    """Generate PDF for multiple processes"""
    process_ids = request.GET.getlist('ids')
    if not process_ids:
        return HttpResponse('No processes selected', status=400)
    
    # Filter by module if specified
    selected_module_id = request.GET.get('module')
    if selected_module_id:
        try:
            selected_module = Module.objects.get(id=selected_module_id)
            processes = Process.objects.filter(id__in=process_ids, module=selected_module).order_by('order')
        except Module.DoesNotExist:
            processes = Process.objects.filter(id__in=process_ids).order_by('order')
    else:
        processes = Process.objects.filter(id__in=process_ids).order_by('order')
    
    if not processes.exists():
        return HttpResponse('No valid processes found', status=400)
    
    # Get history data if included
    history_data = []
    if request.GET.get('include_history') == 'true':
        try:
            history_json = request.GET.get('history_data', '[]')
            history_data = json.loads(history_json)
        except (json.JSONDecodeError, TypeError):
            history_data = []
    
    # Render template
    html_string = render_to_string('process_creator/bulk_print.html', {
        'processes': processes,
        'history_data': history_data
    })
    
    def link_callback(uri, rel):
        sUrl = settings.STATIC_URL
        sRoot = settings.STATIC_ROOT
        mUrl = settings.MEDIA_URL
        mRoot = settings.MEDIA_ROOT

        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            path = os.path.join(settings.BASE_DIR, uri)

        if not os.path.isfile(path):
            return uri
        return path

    response = HttpResponse(content_type='application/pdf')
    pdf_io = BytesIO()
    pisa.CreatePDF(src=html_string, dest=pdf_io, link_callback=link_callback, encoding='utf-8')
    pdf_io.seek(0)

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"Bulk-Process-Report-{timestamp}.pdf"
    
    response = HttpResponse(pdf_io.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{quote(filename)}"'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
@require_app_access('process_creator', action='view')
def bulk_word(request):
    """Generate Word document for multiple processes"""
    process_ids = request.GET.getlist('ids')
    if not process_ids:
        return HttpResponse('No processes selected', status=400)
    
    # Filter by module if specified
    selected_module_id = request.GET.get('module')
    if selected_module_id:
        try:
            selected_module = Module.objects.get(id=selected_module_id)
            processes = Process.objects.filter(id__in=process_ids, module=selected_module).order_by('order')
        except Module.DoesNotExist:
            processes = Process.objects.filter(id__in=process_ids).order_by('order')
    else:
        processes = Process.objects.filter(id__in=process_ids).order_by('order')
    
    if not processes.exists():
        return HttpResponse('No valid processes found', status=400)
    
    # Get history data if included
    history_data = []
    if request.GET.get('include_history') == 'true':
        try:
            history_json = request.GET.get('history_data', '[]')
            history_data = json.loads(history_json)
        except (json.JSONDecodeError, TypeError):
            history_data = []
    
    doc = Document()
    
    # Add title
    title = doc.add_heading('Bulk Process Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add each process
    for i, process in enumerate(processes, 1):
        if i > 1:
            doc.add_page_break()
        
        # Process name
        process_heading = doc.add_heading(f'{i}. {process.name}', level=1)
        
        # Description
        if process.description:
            doc.add_heading('Description', level=2)
            p = doc.add_paragraph(process.description)
            p.paragraph_format.space_after = Inches(0.1)
            p.paragraph_format.line_spacing = 1.15
        
        # Steps
        if process.steps.exists():
            doc.add_heading('Steps', level=2)
            for step in process.steps.all():
                step_heading = doc.add_heading(f'{step.order}. {step.title}', level=3)
                
                if step.details:
                    p = doc.add_paragraph(step.details)
                    p.paragraph_format.space_after = Inches(0.1)
                    p.paragraph_format.line_spacing = 1.15
                
                # Images
                if step.images.exists():
                    for img in step.images.all():
                        try:
                            img_path = os.path.join(settings.MEDIA_ROOT, str(img.image))
                            if os.path.exists(img_path):
                                table = doc.add_table(rows=1, cols=1)
                                table.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                cell = table.cell(0, 0)
                                cell.vertical_alignment = WD_ALIGN_PARAGRAPH.CENTER
                                
                                paragraph = cell.paragraphs[0]
                                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                run = paragraph.add_run()
                                run.add_picture(img_path, width=Inches(6))
                                
                                # Add border
                                from docx.oxml.shared import OxmlElement, qn
                                tc = cell._tc
                                tcPr = tc.get_or_add_tcPr()
                                tcBorders = OxmlElement('w:tcBorders')
                                for border_name in ['top', 'left', 'bottom', 'right']:
                                    border = OxmlElement(f'w:{border_name}')
                                    border.set(qn('w:val'), 'single')
                                    border.set(qn('w:sz'), '12')
                                    border.set(qn('w:space'), '0')
                                    border.set(qn('w:color'), '333333')
                                    tcBorders.append(border)
                                tcPr.append(tcBorders)
                        except Exception as e:
                            pass
        
        # Notes
        if process.notes:
            doc.add_heading('Notes', level=2)
            p = doc.add_paragraph(process.notes)
            p.paragraph_format.space_after = Inches(0.1)
            p.paragraph_format.line_spacing = 1.15
    
    # Add history section if history data is provided
    if history_data:
        doc.add_page_break()
        doc.add_heading('History', level=1)
        
        for i, history_item in enumerate(history_data, 1):
            # History item title
            history_heading = doc.add_heading(f'{i}. {history_item.get("type", "Unknown")} - {history_item.get("date", "")}', level=2)
            
            # History content
            content = history_item.get('content', '')
            if content:
                p = doc.add_paragraph(content)
                p.paragraph_format.space_after = Inches(0.1)
                p.paragraph_format.line_spacing = 1.15
    
    doc_io = BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"Bulk-Process-Report-{timestamp}.docx"
    
    response = HttpResponse(doc_io.getvalue(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="{quote(filename)}"'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

# Create your views here.
