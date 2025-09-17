from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import (Flow, FlowStep, Project, ProjectStep, FlowDependency, 
                    SubFlow, SubFlowStep, ProjectSubFlowStep)
from .utils import get_flow_apps

@login_required
def step_detail(request, app_name):
    """View for individual workflow step - shows all projects at this step"""
    try:
        # Get the flow step with subflows
        flow_step = get_object_or_404(FlowStep, app_name=app_name, is_active=True)
        
        # Get all projects that are currently at this step
        project_steps = ProjectStep.objects.filter(
            flow_step=flow_step,
            project__status__in=['not_started', 'in_progress', 'on_hold']
        ).select_related('project', 'assigned_to').order_by('-created_at')
        
        # Get projects that can start this step (dependencies met)
        can_start_projects = []
        for project_step in project_steps:
            if project_step.can_start and project_step.status == 'pending':
                can_start_projects.append(project_step)
        
        # Get projects currently in progress at this step
        in_progress_projects = project_steps.filter(status='in_progress')
        
        # Get projects blocked at this step
        blocked_projects = project_steps.filter(status='blocked')
        
        # Get projects completed at this step (recent)
        completed_projects = ProjectStep.objects.filter(
            flow_step=flow_step,
            status='completed'
        ).select_related('project').order_by('-actual_completion_date')[:10]
        
        # Get subflows for this step
        subflows = flow_step.subflows.filter(is_active=True).prefetch_related('steps')
        
        context = {
            'flow_step': flow_step,
            'can_start_projects': can_start_projects,
            'in_progress_projects': in_progress_projects,
            'blocked_projects': blocked_projects,
            'completed_projects': completed_projects,
            'total_projects': project_steps.count(),
            'subflows': subflows,
        }
        
        return render(request, 'flow/step_detail.html', context)
        
    except FlowStep.DoesNotExist:
        messages.error(request, f"No active workflow step found for {app_name}")
        return redirect('home')

@login_required
def project_detail(request, project_id):
    """View for individual project details"""
    project = get_object_or_404(Project, id=project_id)
    project_steps = project.project_steps.all().order_by('flow_step__order')
    
    # Calculate completed steps count
    completed_steps_count = project.project_steps.filter(status='completed').count()
    total_steps_count = project.project_steps.count()
    
    context = {
        'project': project,
        'project_steps': project_steps,
        'completed_steps_count': completed_steps_count,
        'total_steps_count': total_steps_count,
    }
    
    return render(request, 'flow/project_detail.html', context)

@login_required
def start_project_step(request, project_step_id):
    """Start a project step"""
    project_step = get_object_or_404(ProjectStep, id=project_step_id)
    
    if not project_step.can_start:
        messages.error(request, "This step cannot be started yet - dependencies not met")
        return redirect('flow:step_detail', app_name=project_step.flow_step.app_name)
    
    if project_step.status != 'pending':
        messages.error(request, "This step is not in pending status")
        return redirect('flow:step_detail', app_name=project_step.flow_step.app_name)
    
    # Start the step
    project_step.status = 'in_progress'
    project_step.start_date = timezone.now()
    project_step.assigned_to = request.user
    project_step.save()
    
    # Update project status if this is the first step
    if project_step.flow_step.order == 1 and project_step.project.status == 'not_started':
        project_step.project.status = 'in_progress'
        project_step.project.start_date = timezone.now()
        project_step.project.save()
    
    messages.success(request, f"Started {project_step.flow_step.step_name} for project {project_step.project.name}")
    return redirect('flow:step_detail', app_name=project_step.flow_step.app_name)

@login_required
def complete_project_step(request, project_step_id):
    """Complete a project step"""
    project_step = get_object_or_404(ProjectStep, id=project_step_id)
    
    if project_step.status != 'in_progress':
        messages.error(request, "This step is not in progress")
        return redirect('flow:step_detail', app_name=project_step.flow_step.app_name)
    
    # Complete the step
    project_step.status = 'completed'
    project_step.actual_completion_date = timezone.now()
    project_step.save()
    
    # Check if this was the last step
    remaining_steps = project_step.project.project_steps.filter(
        status__in=['pending', 'in_progress']
    ).exclude(id=project_step.id)
    
    if not remaining_steps.exists():
        # Project is complete
        project_step.project.status = 'completed'
        project_step.project.actual_completion_date = timezone.now()
        project_step.project.save()
        messages.success(request, f"Project {project_step.project.name} completed!")
    else:
        messages.success(request, f"Completed {project_step.flow_step.step_name} for project {project_step.project.name}")
    
    return redirect('flow:step_detail', app_name=project_step.flow_step.app_name)

@login_required
def block_project_step(request, project_step_id):
    """Block a project step"""
    project_step = get_object_or_404(ProjectStep, id=project_step_id)
    
    if project_step.status not in ['pending', 'in_progress']:
        messages.error(request, "This step cannot be blocked")
        return redirect('flow:step_detail', app_name=project_step.flow_step.app_name)
    
    project_step.status = 'blocked'
    project_step.save()
    
    messages.warning(request, f"Blocked {project_step.flow_step.step_name} for project {project_step.project.name}")
    return redirect('flow:step_detail', app_name=project_step.flow_step.app_name)

@login_required
def unblock_project_step(request, project_step_id):
    """Unblock a project step"""
    project_step = get_object_or_404(ProjectStep, id=project_step_id)
    
    if project_step.status != 'blocked':
        messages.error(request, "This step is not blocked")
        return redirect('flow:step_detail', app_name=project_step.flow_step.app_name)
    
    project_step.status = 'pending'
    project_step.save()
    
    messages.success(request, f"Unblocked {project_step.flow_step.step_name} for project {project_step.project.name}")
    return redirect('flow:step_detail', app_name=project_step.flow_step.app_name)

def create_project_with_scheduling(project_name, project_description, assigned_user=None, start_date=None):
    """Create a new project with automatic scheduling based on flow durations"""
    if start_date is None:
        start_date = timezone.now()
    
    # Get the main flow
    flow = Flow.objects.filter(is_active=True).first()
    if not flow:
        return None
    
    # Get flow steps in order
    flow_steps = FlowStep.objects.filter(flow=flow, is_active=True).order_by('order')
    if not flow_steps.exists():
        return None

    # Create the project
    project = Project.objects.create(
        name=project_name,
        description=project_description,
        flow=flow,
        created_by=User.objects.filter(is_superuser=True).first(),
        assigned_to=assigned_user,
        status='not_started',
        start_date=start_date
    )

    # Calculate scheduling
    current_date = start_date
    total_duration = timedelta(0)

    for flow_step in flow_steps:
        # Calculate target completion date for this main step
        step_duration = flow_step.estimated_duration
        target_completion = current_date + step_duration
        total_duration += step_duration

        # Create project step
        project_step = ProjectStep.objects.create(
            project=project,
            flow_step=flow_step,
            status='pending',
            assigned_to=assigned_user,
            target_completion_date=target_completion
        )

        # Create subflow steps for this main step
        subflows = SubFlow.objects.filter(main_flow_step=flow_step, is_active=True)
        subflow_current_date = current_date

        for subflow in subflows:
            subflow_steps = SubFlowStep.objects.filter(subflow=subflow, is_active=True).order_by('order')
            
            for subflow_step in subflow_steps:
                # Calculate target completion date for this subflow step
                subflow_step_duration = subflow_step.estimated_duration
                subflow_target_completion = subflow_current_date + subflow_step_duration

                # Create project subflow step
                project_subflow_step = ProjectSubFlowStep.objects.create(
                    project=project,
                    subflow_step=subflow_step,
                    status='pending',
                    assigned_to=assigned_user,
                    target_completion_date=subflow_target_completion
                )
                
                # Move to next subflow step (finish-to-start dependency)
                subflow_current_date = subflow_target_completion

        # Move to next main step (finish-to-start dependency)
        current_date = target_completion

    # Set project target completion date
    project.target_completion_date = start_date + total_duration
    project.save()

    return project

@login_required
def create_new_project(request):
    """Create a new project with automatic scheduling"""
    if request.method == 'POST':
        project_name = request.POST.get('name')
        project_description = request.POST.get('description', '')
        assigned_user = request.user if request.POST.get('assign_to_me') else None
        
        if not project_name:
            messages.error(request, "Project name is required")
            return redirect('home')
        
        # Create project with scheduling
        project = create_project_with_scheduling(
            project_name=project_name,
            project_description=project_description,
            assigned_user=assigned_user
        )
        
        if project:
            messages.success(request, f"Created project '{project.name}' with automatic scheduling")
            return redirect('flow:step_detail', app_name='approval_prints')
        else:
            messages.error(request, "Failed to create project. Please check flow configuration.")
            return redirect('home')
    
    return render(request, 'flow/create_project.html')

@login_required
def step_detail_page(request, app_name):
    """Detailed page for individual workflow step with all information and processes"""
    try:
        # Get the flow step with subflows
        flow_step = get_object_or_404(FlowStep, app_name=app_name, is_active=True)
        
        # Get all projects that are currently at this step
        project_steps = ProjectStep.objects.filter(
            flow_step=flow_step,
            project__status__in=['not_started', 'in_progress', 'on_hold']
        ).select_related('project', 'assigned_to').order_by('-created_at')
        
        # Get subflows for this step
        subflows = SubFlow.objects.filter(main_flow_step=flow_step, is_active=True).prefetch_related('steps')
        
        # Get completed projects for this step
        completed_projects = ProjectStep.objects.filter(
            flow_step=flow_step,
            project__status='completed'
        ).select_related('project', 'assigned_to').order_by('-actual_completion_date')[:10]
        
        # Get step statistics
        total_projects = project_steps.count()
        in_progress_count = project_steps.filter(status='in_progress').count()
        pending_count = project_steps.filter(status='pending').count()
        blocked_count = project_steps.filter(status='blocked').count()
        completed_count = completed_projects.count()
        
        context = {
            'title': f'{flow_step.step_name} - Detailed View',
            'flow_step': flow_step,
            'project_steps': project_steps,
            'subflows': subflows,
            'completed_projects': completed_projects,
            'total_projects': total_projects,
            'in_progress_count': in_progress_count,
            'pending_count': pending_count,
            'blocked_count': blocked_count,
            'completed_count': completed_count,
        }
        
        return render(request, f'flow/step_pages/{app_name}.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading step details: {str(e)}")
        return redirect('home')