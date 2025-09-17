from django.contrib import admin
from .models import Process, Step


class StepInline(admin.TabularInline):
    model = Step
    extra = 1
    fields = ("order", "title", "details")
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

# Register your models here.
