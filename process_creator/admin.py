from django.contrib import admin
from .models import Module, Process, Step, StepImage, StepLink, StepFile, AIInteraction, ProcessTemplate, TemplateStep, Job, JobStep, JobSubtask, JobStepImage


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name", "description")
    ordering = ("name",)


class StepInline(admin.TabularInline):
    model = Step
    extra = 1
    fields = ("order", "title", "details")
    ordering = ("order",)

class StepImageInline(admin.TabularInline):
    model = StepImage
    extra = 0
    fields = ("order", "image")
    ordering = ("order",)

class StepLinkInline(admin.TabularInline):
    model = StepLink
    extra = 0
    fields = ("order", "title", "url")
    ordering = ("order",)

class StepFileInline(admin.TabularInline):
    model = StepFile
    extra = 0
    fields = ("order", "file")
    ordering = ("order",)


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ("name", "module", "updated_at")
    list_filter = ("module",)
    search_fields = ("name", "module__name")
    inlines = [StepInline]


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ("process", "order", "title")
    list_filter = ("process",)
    ordering = ("process", "order")
    inlines = [StepImageInline, StepLinkInline, StepFileInline]


@admin.register(AIInteraction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ['process', 'interaction_type', 'tokens_used', 'cost', 'created_at']
    list_filter = ['interaction_type', 'created_at']
    search_fields = ['process__name', 'prompt_sent', 'response_received']
    readonly_fields = ['created_at', 'tokens_used', 'cost']
    ordering = ['-created_at']

# New admin registrations

class TemplateStepInline(admin.TabularInline):
    model = TemplateStep
    extra = 0
    fields = ("order", "title", "details")
    ordering = ("order",)

@admin.register(ProcessTemplate)
class ProcessTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "module", "version", "source_process", "updated_at", "is_active")
    list_filter = ("module", "is_active")
    search_fields = ("name", "module__name", "source_process__name")
    inlines = [TemplateStepInline]
    ordering = ("-updated_at",)

class JobStepInline(admin.TabularInline):
    model = JobStep
    extra = 0
    fields = ("order", "title", "status", "assigned_to", "started_at", "completed_at")
    ordering = ("order",)
    readonly_fields = ("started_at", "completed_at")

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("name", "template", "status", "assigned_to", "created_at", "started_at", "completed_at")
    list_filter = ("status", "template__module")
    search_fields = ("name", "template__name", "template__source_process__name")
    inlines = [JobStepInline]
    ordering = ("-created_at",)

@admin.register(JobStep)
class JobStepAdmin(admin.ModelAdmin):
    list_display = ("job", "order", "title", "status", "assigned_to", "started_at", "completed_at")
    list_filter = ("status", "job")
    ordering = ("job", "order")

@admin.register(JobSubtask)
class JobSubtaskAdmin(admin.ModelAdmin):
    list_display = ("job_step", "order", "text", "completed")
    list_filter = ("completed",)
    ordering = ("job_step", "order")

@admin.register(JobStepImage)
class JobStepImageAdmin(admin.ModelAdmin):
    list_display = ("job_step", "subtask_index", "order", "uploaded_at")
    list_filter = ("job_step",)
    ordering = ("job_step", "order")
