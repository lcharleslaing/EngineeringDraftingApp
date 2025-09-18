from django.contrib import admin
from .models import Module, Process, Step, StepImage, StepLink, StepFile, AIInteraction


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

# Register your models here.
