from django.contrib import admin
from .models import Process, Step, StepImage, AIInteraction


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


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at")
    search_fields = ("name",)
    inlines = [StepInline]


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ("process", "order", "title")
    list_filter = ("process",)
    ordering = ("process", "order")
    inlines = [StepImageInline]


@admin.register(AIInteraction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ['process', 'interaction_type', 'tokens_used', 'cost', 'created_at']
    list_filter = ['interaction_type', 'created_at']
    search_fields = ['process__name', 'prompt_sent', 'response_received']
    readonly_fields = ['created_at', 'tokens_used', 'cost']
    ordering = ['-created_at']

# Register your models here.
