"""Flow Calculation admin configuration."""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import FlowProject, FlowStep, FlowCalculation


@admin.register(FlowProject)
class FlowProjectAdmin(admin.ModelAdmin):
    """Admin for FlowProject model."""
    
    list_display = ['name', 'start_date', 'duration_days', 'end_date', 'calculated_end_date', 
                   'is_delayed', 'delay_days', 'created_by', 'created_at']
    list_filter = ['created_at', 'start_date', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['end_date', 'calculated_end_date', 'is_delayed', 'delay_days', 
                      'created_at', 'updated_at']
    fieldsets = [
        ('Project Information', {
            'fields': ['name', 'description', 'created_by']
        }),
        ('Timeline', {
            'fields': ['start_date', 'duration_days', 'end_date']
        }),
        ('Calculated Results', {
            'fields': ['calculated_end_date', 'is_delayed', 'delay_days'],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def is_delayed(self, obj):
        """Display delay status with color coding."""
        if obj.is_delayed:
            return format_html('<span style="color: red; font-weight: bold;">Yes ({} days)</span>', obj.delay_days)
        return format_html('<span style="color: green;">No</span>')
    is_delayed.short_description = 'Delayed'
    
    def delay_days(self, obj):
        """Display delay days."""
        return obj.delay_days
    delay_days.short_description = 'Delay (days)'


class FlowStepInline(admin.TabularInline):
    """Inline admin for FlowStep model."""
    
    model = FlowStep
    extra = 0
    fields = ['name', 'duration_days', 'start_date', 'end_date', 'dependencies']
    readonly_fields = ['start_date', 'end_date']
    autocomplete_fields = ['dependencies']


@admin.register(FlowStep)
class FlowStepAdmin(admin.ModelAdmin):
    """Admin for FlowStep model."""
    
    list_display = ['name', 'project', 'duration_days', 'start_date', 'end_date', 
                   'is_critical_path', 'slack_days']
    list_filter = ['project', 'start_date']
    search_fields = ['name', 'description', 'project__name']
    readonly_fields = ['start_date', 'end_date', 'is_critical_path', 'slack_days', 
                      'calculated_start_date', 'calculated_end_date', 'created_at', 'updated_at']
    autocomplete_fields = ['project', 'dependencies']
    fieldsets = [
        ('Step Information', {
            'fields': ['project', 'name', 'description', 'duration_days']
        }),
        ('Dependencies', {
            'fields': ['dependencies']
        }),
        ('Calculated Dates', {
            'fields': ['start_date', 'end_date', 'calculated_start_date', 'calculated_end_date'],
            'classes': ['collapse']
        }),
        ('Analysis', {
            'fields': ['is_critical_path', 'slack_days'],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def is_critical_path(self, obj):
        """Display critical path status with color coding."""
        if obj.is_critical_path:
            return format_html('<span style="color: red; font-weight: bold;">Yes</span>')
        return format_html('<span style="color: green;">No</span>')
    is_critical_path.short_description = 'Critical Path'
    
    def slack_days(self, obj):
        """Display slack days with color coding."""
        slack = obj.slack_days
        if slack > 0:
            return format_html('<span style="color: green;">{} days</span>', slack)
        elif slack == 0:
            return format_html('<span style="color: orange;">0 days</span>')
        else:
            return format_html('<span style="color: red;">{} days (overdue)</span>', slack)
    slack_days.short_description = 'Slack Time'


@admin.register(FlowCalculation)
class FlowCalculationAdmin(admin.ModelAdmin):
    """Admin for FlowCalculation model."""
    
    list_display = ['project', 'calculated_at', 'total_duration_days', 'is_valid', 'critical_path_count']
    list_filter = ['calculated_at', 'is_valid', 'project']
    search_fields = ['project__name']
    readonly_fields = ['calculated_at', 'critical_path_steps', 'critical_path_count']
    fieldsets = [
        ('Calculation Information', {
            'fields': ['project', 'calculated_at', 'total_duration_days', 'is_valid']
        }),
        ('Results', {
            'fields': ['critical_path_steps', 'critical_path_count'],
            'classes': ['collapse']
        }),
        ('Error Information', {
            'fields': ['error_message'],
            'classes': ['collapse']
        })
    ]
    
    def critical_path_count(self, obj):
        """Display number of critical path steps."""
        return obj.critical_path_steps.count()
    critical_path_count.short_description = 'Critical Path Steps'


# Update FlowProjectAdmin to include inline steps
FlowProjectAdmin.inlines = [FlowStepInline]