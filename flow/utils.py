from django.db import models
from django.utils import timezone
from datetime import timedelta
from .models import Flow, FlowStep, Project, ProjectStep, FlowDependency, FlowCategory

def get_flow_apps():
    """Get all apps that are part of flows"""
    flow_steps = FlowStep.objects.filter(is_active=True).values_list('app_name', flat=True).distinct()
    return list(flow_steps)

def get_non_flow_apps():
    """Get all apps that are not part of flows"""
    from rbac.models import AVAILABLE_APPS
    flow_apps = get_flow_apps()
    all_apps = [app[0] for app in AVAILABLE_APPS]
    return [app for app in all_apps if app not in flow_apps]

def create_default_engineering_flow():
    """Create the default engineering flow with the specified steps"""
    from django.contrib.auth.models import User
    
    # Get or create flow category
    category, created = FlowCategory.objects.get_or_create(
        name='Engineering',
        defaults={
            'description': 'Engineering workflow processes',
            'color': '#10B981',
            'icon': 'fas fa-cogs'
        }
    )
    
    # Get or create the main engineering flow
    flow, created = Flow.objects.get_or_create(
        name='Engineering Drafting Flow',
        defaults={
            'description': 'Complete engineering drafting workflow from approval to purchasing',
            'category': category,
            'created_by': User.objects.filter(is_superuser=True).first()
        }
    )
    
    if created:
        # Define the flow steps in order
        steps_data = [
            ('approval_prints', 'Approval Prints', 'Initial approval and review of prints', timedelta(days=2)),
            ('prints_to_customer', 'Prints to Customer', 'Send approved prints to customer', timedelta(days=1)),
            ('long_lead_release', 'Long Lead Release', 'Release long lead items for procurement', timedelta(days=3)),
            ('drafting_queue', 'Drafting Queue', 'Queue items for drafting process', timedelta(days=5)),
            ('engineering_review_and_release', 'Engineering Review & Release', 'Engineering review and final release', timedelta(days=3)),
            ('release_to_purchasing', 'Release to Purchasing', 'Final release to purchasing department', timedelta(days=1)),
        ]
        
        # Create flow steps
        for order, (app_name, step_name, description, duration) in enumerate(steps_data, 1):
            FlowStep.objects.create(
                flow=flow,
                app_name=app_name,
                step_name=step_name,
                description=description,
                order=order,
                estimated_duration=duration,
                is_required=True
            )
        
        # Create dependencies (each step depends on the previous one)
        steps = FlowStep.objects.filter(flow=flow).order_by('order')
        for i in range(1, len(steps)):
            FlowDependency.objects.create(
                flow=flow,
                predecessor=steps[i-1],
                successor=steps[i],
                dependency_type='finish_to_start',
                lag_time=timedelta(0)
            )
    
    return flow

def calculate_project_timeline(project):
    """Calculate the timeline for a project based on flow steps and dependencies"""
    if not project.flow:
        return None
    
    steps = FlowStep.objects.filter(flow=project.flow, is_active=True).order_by('order')
    timeline = []
    current_date = project.start_date or timezone.now()
    
    for step in steps:
        # Calculate when this step can start
        dependencies = FlowDependency.objects.filter(
            successor=step,
            is_active=True
        ).select_related('predecessor')
        
        start_date = current_date
        for dep in dependencies:
            # Find the predecessor step's completion time
            pred_step = steps.filter(id=dep.predecessor.id).first()
            if pred_step:
                # This is simplified - in reality, you'd need to track actual completion times
                pred_duration = pred_step.estimated_duration
                pred_start = start_date - pred_duration
                start_date = max(start_date, pred_start + pred_duration + dep.lag_time)
        
        end_date = start_date + step.estimated_duration
        
        timeline.append({
            'step': step,
            'start_date': start_date,
            'end_date': end_date,
            'duration': step.estimated_duration
        })
        
        current_date = end_date
    
    return timeline

def get_flow_progress(project):
    """Get detailed progress information for a project"""
    if not project.flow:
        return None
    
    steps = ProjectStep.objects.filter(project=project).select_related('flow_step').order_by('flow_step__order')
    total_steps = steps.count()
    completed_steps = steps.filter(status='completed').count()
    in_progress_steps = steps.filter(status='in_progress').count()
    blocked_steps = steps.filter(status='blocked').count()
    
    return {
        'total_steps': total_steps,
        'completed_steps': completed_steps,
        'in_progress_steps': in_progress_steps,
        'blocked_steps': blocked_steps,
        'progress_percentage': (completed_steps / total_steps * 100) if total_steps > 0 else 0,
        'steps': steps
    }

def can_start_step(project_step):
    """Check if a project step can be started"""
    return project_step.can_start

def get_next_available_steps(project):
    """Get the next steps that can be started in a project"""
    steps = ProjectStep.objects.filter(
        project=project,
        status='pending'
    ).select_related('flow_step').order_by('flow_step__order')
    
    available_steps = []
    for step in steps:
        if can_start_step(step):
            available_steps.append(step)
        else:
            # If we hit a step that can't start, stop here
            break
    
    return available_steps

def get_overdue_projects():
    """Get all overdue projects"""
    return Project.objects.filter(
        target_completion_date__lt=timezone.now(),
        status__in=['not_started', 'in_progress', 'on_hold']
    )

def get_overdue_steps():
    """Get all overdue project steps"""
    return ProjectStep.objects.filter(
        target_completion_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    )
