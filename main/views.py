from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from flow.models import Flow, FlowStep, ProjectStep, SubFlow
from datetime import timedelta

def format_duration(duration):
    """Format a timedelta duration for display"""
    if not duration:
        return "N/A"
    
    if isinstance(duration, timedelta):
        total_days = duration.days
        if total_days == 0:
            hours = duration.seconds // 3600
            if hours == 0:
                minutes = duration.seconds // 60
                return f"{minutes}m" if minutes > 0 else "0m"
            return f"{hours}h"
        elif total_days < 7:
            return f"{total_days}d"
        else:
            weeks = total_days // 7
            remaining_days = total_days % 7
            if remaining_days == 0:
                return f"{weeks}w"
            else:
                return f"{weeks}w {remaining_days}d"
    return str(duration)

def home(request):
    """Homepage dashboard view"""
    # Get the main engineering flow and its steps
    try:
        main_flow = Flow.objects.filter(is_active=True).first()
        flow_steps = FlowStep.objects.filter(flow=main_flow, is_active=True).order_by('order') if main_flow else []
        
        # Add formatted duration and statistics to each step
        for step in flow_steps:
            step.formatted_duration = format_duration(step.estimated_duration)
            
            # Get project statistics for this step
            project_steps = ProjectStep.objects.filter(flow_step=step)
            step.total_projects = project_steps.count()
            step.in_progress_count = project_steps.filter(status='in_progress').count()
            step.pending_count = project_steps.filter(status='pending').count()
            step.completed_count = project_steps.filter(status='completed').count()
            step.blocked_count = project_steps.filter(status='blocked').count()
            
            # Get subflow count
            step.subflow_count = SubFlow.objects.filter(main_flow_step=step, is_active=True).count()
            
    except:
        main_flow = None
        flow_steps = []
    
    context = {
        'title': 'Dashboard',
        'user': request.user,
        'main_flow': main_flow,
        'flow_steps': flow_steps,
    }
    return render(request, 'main/home.html', context)
