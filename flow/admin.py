from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    FlowCategory, Flow, FlowStep, FlowDependency, 
    Project, ProjectStep, FlowTemplate,
    SubFlow, SubFlowStep, SubFlowDependency, ProjectSubFlowStep
)

class FlowStepInline(admin.TabularInline):
    model = FlowStep
    extra = 0
    fields = ('app_name', 'step_name', 'order', 'estimated_duration', 'is_required', 'is_active')
    ordering = ['order']

class FlowDependencyInline(admin.TabularInline):
    model = FlowDependency
    extra = 0
    fields = ('predecessor', 'successor', 'dependency_type', 'lag_time', 'is_active')
    fk_name = 'flow'

@admin.register(FlowCategory)
class FlowCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_display', 'icon', 'is_active', 'flows_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'
    
    def flows_count(self, obj):
        count = obj.flows.count()
        return format_html('<span style="color: green;">{}</span>', count)
    flows_count.short_description = 'Flows'

@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'steps_count', 'projects_count', 'created_at')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [FlowStepInline, FlowDependencyInline]
    
    def steps_count(self, obj):
        count = obj.steps.count()
        return format_html('<span style="color: blue;">{}</span>', count)
    steps_count.short_description = 'Steps'
    
    def projects_count(self, obj):
        count = obj.projects.count()
        return format_html('<span style="color: green;">{}</span>', count)
    projects_count.short_description = 'Projects'

@admin.register(FlowStep)
class FlowStepAdmin(admin.ModelAdmin):
    list_display = ('step_name', 'flow', 'app_name', 'order', 'estimated_duration', 'is_required', 'is_active')
    list_filter = ('is_active', 'is_required', 'flow', 'app_name')
    search_fields = ('step_name', 'description', 'app_name')
    ordering = ['flow', 'order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('flow')

class ProjectStepInline(admin.TabularInline):
    model = ProjectStep
    extra = 0
    fields = ('flow_step', 'status', 'assigned_to', 'start_date', 'target_completion_date', 'actual_completion_date')
    readonly_fields = ('flow_step',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'flow', 'status', 'assigned_to', 'progress_display', 'is_overdue_display', 'created_at')
    list_filter = ('status', 'flow', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'progress_display')
    inlines = [ProjectStepInline]
    
    def progress_display(self, obj):
        progress = obj.progress_percentage
        color = 'green' if progress == 100 else 'blue' if progress > 0 else 'gray'
        return format_html(
            '<div style="width: 100px; background-color: #e5e7eb; border-radius: 4px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">{}%</div>'
            '</div>',
            progress, color, f"{progress:.1f}"
        )
    progress_display.short_description = 'Progress'
    
    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">⚠️ Overdue</span>')
        return format_html('<span style="color: green;">✓ On Time</span>')
    is_overdue_display.short_description = 'Status'

@admin.register(ProjectStep)
class ProjectStepAdmin(admin.ModelAdmin):
    list_display = ('project', 'flow_step', 'status', 'assigned_to', 'is_overdue_display', 'created_at')
    list_filter = ('status', 'flow_step__flow', 'created_at')
    search_fields = ('project__name', 'flow_step__step_name', 'notes')
    ordering = ['project', 'flow_step__order']
    
    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">⚠️ Overdue</span>')
        return format_html('<span style="color: green;">✓ On Time</span>')
    is_overdue_display.short_description = 'Status'

@admin.register(FlowDependency)
class FlowDependencyAdmin(admin.ModelAdmin):
    list_display = ('predecessor', 'successor', 'dependency_type', 'lag_time', 'is_active')
    list_filter = ('dependency_type', 'is_active', 'flow')
    search_fields = ('predecessor__step_name', 'successor__step_name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('predecessor', 'successor', 'flow')

@admin.register(FlowTemplate)
class FlowTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_public', 'created_by', 'created_at')
    list_filter = ('is_public', 'category', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)

class SubFlowStepInline(admin.TabularInline):
    model = SubFlowStep
    extra = 0
    fields = ('step_name', 'order', 'estimated_duration', 'is_required', 'is_active')
    ordering = ['order']

class SubFlowDependencyInline(admin.TabularInline):
    model = SubFlowDependency
    extra = 0
    fields = ('predecessor', 'successor', 'dependency_type', 'lag_time', 'is_active')
    fk_name = 'subflow'

@admin.register(SubFlow)
class SubFlowAdmin(admin.ModelAdmin):
    list_display = ('name', 'main_flow_step', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'main_flow_step__flow', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ['main_flow_step', 'name']
    inlines = [SubFlowStepInline, SubFlowDependencyInline]

@admin.register(SubFlowStep)
class SubFlowStepAdmin(admin.ModelAdmin):
    list_display = ('step_name', 'subflow', 'order', 'estimated_duration', 'is_required', 'is_active')
    list_filter = ('is_active', 'is_required', 'subflow__main_flow_step')
    search_fields = ('step_name', 'description')
    ordering = ['subflow', 'order']

@admin.register(ProjectSubFlowStep)
class ProjectSubFlowStepAdmin(admin.ModelAdmin):
    list_display = ('project', 'subflow_step', 'status', 'assigned_to', 'is_overdue_display', 'created_at')
    list_filter = ('status', 'subflow_step__subflow__main_flow_step', 'created_at')
    search_fields = ('project__name', 'subflow_step__step_name', 'notes')
    ordering = ['project', 'subflow_step__order']
    
    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">⚠️ Overdue</span>')
        return format_html('<span style="color: green;">✓ On Time</span>')
    is_overdue_display.short_description = 'Status'

# Customize admin site
admin.site.site_header = "Drafting Engineering Flow - Flow Management"
admin.site.site_title = "DEF Flow Admin"
admin.site.index_title = "Workflow and Project Management"
