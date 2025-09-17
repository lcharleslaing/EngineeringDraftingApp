"""Flow Calculation views."""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import FlowProject, FlowStep, FlowCalculation
from .forms import FlowProjectForm, FlowStepForm, FlowStepQuickAddForm, FlowCalculationForm


class FlowProjectListView(LoginRequiredMixin, ListView):
    """List view for flow projects."""
    
    model = FlowProject
    template_name = 'flow_calc/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20
    
    def get_queryset(self):
        """Filter projects by user."""
        return FlowProject.objects.filter(created_by=self.request.user).order_by('-created_at')


class FlowProjectDetailView(LoginRequiredMixin, DetailView):
    """Detail view for flow projects with calculation."""
    
    model = FlowProject
    template_name = 'flow_calc/project_detail.html'
    context_object_name = 'project'
    
    def get_queryset(self):
        """Filter projects by user."""
        return FlowProject.objects.filter(created_by=self.request.user)
    
    def get_context_data(self, **kwargs):
        """Add calculation context."""
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Get all steps ordered by start date
        steps = project.steps.all().order_by('start_date', 'name')
        context['steps'] = steps
        
        # Calculate critical path
        critical_path_steps = []
        if steps.exists():
            latest_end_date = max(step.calculated_end_date for step in steps)
            critical_path_steps = [step for step in steps if step.calculated_end_date == latest_end_date]
        
        context['critical_path_steps'] = critical_path_steps
        context['calculation_form'] = FlowCalculationForm()
        
        return context


class FlowProjectCreateView(LoginRequiredMixin, CreateView):
    """Create view for flow projects."""
    
    model = FlowProject
    form_class = FlowProjectForm
    template_name = 'flow_calc/project_form.html'
    
    def get_form_kwargs(self):
        """Add user to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        """Redirect to project detail after creation."""
        return reverse('flow_calc:project_detail', kwargs={'pk': self.object.pk})


class FlowProjectUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for flow projects."""
    
    model = FlowProject
    form_class = FlowProjectForm
    template_name = 'flow_calc/project_form.html'
    
    def get_queryset(self):
        """Filter projects by user."""
        return FlowProject.objects.filter(created_by=self.request.user)
    
    def get_success_url(self):
        """Redirect to project detail after update."""
        return reverse('flow_calc:project_detail', kwargs={'pk': self.object.pk})


class FlowProjectDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for flow projects."""
    
    model = FlowProject
    template_name = 'flow_calc/project_confirm_delete.html'
    success_url = reverse_lazy('flow_calc:project_list')
    
    def get_queryset(self):
        """Filter projects by user."""
        return FlowProject.objects.filter(created_by=self.request.user)


class FlowStepCreateView(LoginRequiredMixin, CreateView):
    """Create view for flow steps."""
    
    model = FlowStep
    form_class = FlowStepForm
    template_name = 'flow_calc/step_form.html'
    
    def get_project(self):
        """Get the project from URL kwargs."""
        project_id = self.kwargs.get('project_id')
        return get_object_or_404(FlowProject, pk=project_id, created_by=self.request.user)
    
    def get_form_kwargs(self):
        """Add project to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs
    
    def get_success_url(self):
        """Redirect to project detail after creation."""
        return reverse('flow_calc:project_detail', kwargs={'pk': self.get_project().pk})


class FlowStepUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for flow steps."""
    
    model = FlowStep
    form_class = FlowStepForm
    template_name = 'flow_calc/step_form.html'
    
    def get_queryset(self):
        """Filter steps by user's projects."""
        return FlowStep.objects.filter(project__created_by=self.request.user)
    
    def get_form_kwargs(self):
        """Add project to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.object.project
        return kwargs
    
    def get_success_url(self):
        """Redirect to project detail after update."""
        return reverse('flow_calc:project_detail', kwargs={'pk': self.object.project.pk})


class FlowStepDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for flow steps."""
    
    model = FlowStep
    template_name = 'flow_calc/step_confirm_delete.html'
    
    def get_queryset(self):
        """Filter steps by user's projects."""
        return FlowStep.objects.filter(project__created_by=self.request.user)
    
    def get_success_url(self):
        """Redirect to project detail after deletion."""
        return reverse('flow_calc:project_detail', kwargs={'pk': self.object.project.pk})


class FlowStepQuickAddView(LoginRequiredMixin, CreateView):
    """Quick add view for multiple flow steps."""
    
    form_class = FlowStepQuickAddForm
    template_name = 'flow_calc/step_quick_add.html'
    
    def get_project(self):
        """Get the project from URL kwargs."""
        project_id = self.kwargs.get('project_id')
        return get_object_or_404(FlowProject, pk=project_id, created_by=self.request.user)
    
    def get_form_kwargs(self):
        """Add project to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs
    
    def form_valid(self, form):
        """Handle form validation and create steps."""
        try:
            with transaction.atomic():
                created_steps = form.save()
                messages.success(
                    self.request, 
                    f'Successfully created {len(created_steps)} steps.'
                )
        except Exception as e:
            messages.error(self.request, f'Error creating steps: {str(e)}')
            return self.form_invalid(form)
        
        return redirect('flow_calc:project_detail', pk=self.get_project().pk)


class FlowCalculationView(LoginRequiredMixin, TemplateView):
    """View for calculating flow."""
    
    template_name = 'flow_calc/calculation.html'
    
    def get_context_data(self, **kwargs):
        """Add calculation context."""
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(FlowProject, pk=project_id, created_by=self.request.user)
        
        context['project'] = project
        context['calculation_form'] = FlowCalculationForm()
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle calculation request."""
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(FlowProject, pk=project_id, created_by=self.request.user)
        
        form = FlowCalculationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Recalculate all steps
                    for step in project.steps.all():
                        step.calculate_dates()
                    
                    # Create or update calculation record
                    calculation, created = FlowCalculation.objects.get_or_create(
                        project=project,
                        defaults={
                            'total_duration_days': (project.calculated_end_date - project.start_date).days + 1,
                            'is_valid': True
                        }
                    )
                    
                    if not created:
                        calculation.total_duration_days = (project.calculated_end_date - project.start_date).days + 1
                        calculation.is_valid = True
                        calculation.error_message = ''
                        calculation.save()
                    
                    # Update critical path steps
                    critical_steps = []
                    if project.steps.exists():
                        latest_end_date = max(step.calculated_end_date for step in project.steps.all())
                        critical_steps = [step for step in project.steps.all() if step.calculated_end_date == latest_end_date]
                    
                    calculation.critical_path_steps.set(critical_steps)
                    
                    messages.success(request, 'Flow calculation completed successfully!')
                    
            except Exception as e:
                messages.error(request, f'Error during calculation: {str(e)}')
                # Create error calculation record
                FlowCalculation.objects.update_or_create(
                    project=project,
                    defaults={
                        'is_valid': False,
                        'error_message': str(e)
                    }
                )
        
        return redirect('flow_calc:project_detail', pk=project.pk)


class FlowDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard view for flow calculations."""
    
    template_name = 'flow_calc/dashboard.html'
    
    def get_context_data(self, **kwargs):
        """Add dashboard context."""
        context = super().get_context_data(**kwargs)
        
        # Get user's projects
        projects = FlowProject.objects.filter(created_by=self.request.user).order_by('-created_at')[:10]
        context['recent_projects'] = projects
        
        # Get projects with delays
        delayed_projects = [p for p in projects if p.is_delayed]
        context['delayed_projects'] = delayed_projects
        
        # Get total projects count
        context['total_projects'] = FlowProject.objects.filter(created_by=self.request.user).count()
        
        return context


def calculate_flow_api(request, project_id):
    """API endpoint for calculating flow."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        project = get_object_or_404(FlowProject, pk=project_id, created_by=request.user)
        
        with transaction.atomic():
            # Recalculate all steps
            for step in project.steps.all():
                step.calculate_dates()
            
            # Calculate total duration
            total_duration = (project.calculated_end_date - project.start_date).days + 1
            
            # Find critical path
            critical_steps = []
            if project.steps.exists():
                latest_end_date = max(step.calculated_end_date for step in project.steps.all())
                critical_steps = [step.id for step in project.steps.all() if step.calculated_end_date == latest_end_date]
            
            return JsonResponse({
                'success': True,
                'project_id': project.id,
                'calculated_end_date': project.calculated_end_date.isoformat(),
                'total_duration_days': total_duration,
                'is_delayed': project.is_delayed,
                'delay_days': project.delay_days,
                'critical_path_steps': critical_steps
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)