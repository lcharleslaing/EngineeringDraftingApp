"""Flow Calculation models for project flow management."""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class FlowProject(models.Model):
    """A project that contains multiple flow steps."""
    
    name = models.CharField(max_length=200, help_text="Project name")
    description = models.TextField(blank=True, help_text="Project description")
    start_date = models.DateField(help_text="Project start date")
    duration_days = models.PositiveIntegerField(help_text="Total project duration in days")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flow_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Flow Project"
        verbose_name_plural = "Flow Projects"
    
    def __str__(self):
        return self.name
    
    @property
    def end_date(self):
        """Calculate project end date based on start date and duration."""
        return self.start_date + timedelta(days=self.duration_days)
    
    @property
    def calculated_end_date(self):
        """Calculate actual end date based on step dependencies."""
        if not self.steps.exists():
            return self.end_date
        
        # Find the step with the latest calculated end date
        latest_step = self.steps.order_by('-calculated_end_date').first()
        return latest_step.calculated_end_date if latest_step else self.end_date
    
    @property
    def is_delayed(self):
        """Check if project is delayed based on calculated vs planned end date."""
        return self.calculated_end_date > self.end_date
    
    @property
    def delay_days(self):
        """Calculate delay in days."""
        if self.is_delayed:
            return (self.calculated_end_date - self.end_date).days
        return 0


class FlowStep(models.Model):
    """A step within a flow project with dependencies."""
    
    project = models.ForeignKey(FlowProject, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=200, help_text="Step name")
    description = models.TextField(blank=True, help_text="Step description")
    duration_days = models.PositiveIntegerField(help_text="Step duration in days")
    start_date = models.DateField(null=True, blank=True, help_text="Step start date (calculated)")
    end_date = models.DateField(null=True, blank=True, help_text="Step end date (calculated)")
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False, 
                                        related_name='dependent_steps',
                                        help_text="Steps that must complete before this step starts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_date', 'name']
        verbose_name = "Flow Step"
        verbose_name_plural = "Flow Steps"
    
    def __str__(self):
        return f"{self.project.name} - {self.name}"
    
    def clean(self):
        """Validate step dependencies."""
        super().clean()
        
        # Check for circular dependencies
        if self.pk:
            # Get all steps that depend on this step
            dependent_steps = self.dependent_steps.all()
            
            # Check if any dependent step is also a dependency of this step
            for dependent in dependent_steps:
                if self in dependent.dependencies.all():
                    raise ValidationError("Circular dependency detected between steps.")
    
    def save(self, *args, **kwargs):
        """Override save to calculate dates and validate dependencies."""
        self.clean()
        super().save(*args, **kwargs)
        self.calculate_dates()
    
    def calculate_dates(self):
        """Calculate start and end dates based on dependencies."""
        if not self.dependencies.exists():
            # No dependencies - start on project start date
            self.start_date = self.project.start_date
        else:
            # Start after all dependencies complete
            latest_dependency_end = max(
                dep.calculated_end_date for dep in self.dependencies.all()
            )
            self.start_date = latest_dependency_end + timedelta(days=1)
        
        # Calculate end date
        self.end_date = self.start_date + timedelta(days=self.duration_days - 1)
        
        # Update without triggering save() to avoid recursion
        FlowStep.objects.filter(pk=self.pk).update(
            start_date=self.start_date,
            end_date=self.end_date
        )
    
    @property
    def calculated_start_date(self):
        """Get calculated start date."""
        if self.start_date:
            return self.start_date
        self.calculate_dates()
        return self.start_date
    
    @property
    def calculated_end_date(self):
        """Get calculated end date."""
        if self.end_date:
            return self.end_date
        self.calculate_dates()
        return self.end_date
    
    @property
    def is_critical_path(self):
        """Check if this step is on the critical path (affects project end date)."""
        return self.calculated_end_date == self.project.calculated_end_date
    
    @property
    def slack_days(self):
        """Calculate slack time (how much this step can be delayed)."""
        if not self.dependent_steps.exists():
            # No dependent steps - slack is until project end
            return (self.project.end_date - self.calculated_end_date).days
        else:
            # Slack is until the earliest dependent step needs to start
            earliest_dependent_start = min(
                dep.calculated_start_date for dep in self.dependent_steps.all()
            )
            return (earliest_dependent_start - self.calculated_end_date - timedelta(days=1)).days


class FlowCalculation(models.Model):
    """Store calculation results and metadata."""
    
    project = models.OneToOneField(FlowProject, on_delete=models.CASCADE, related_name='calculation')
    calculated_at = models.DateTimeField(auto_now_add=True)
    total_duration_days = models.PositiveIntegerField(help_text="Total calculated project duration")
    critical_path_steps = models.ManyToManyField(FlowStep, blank=True, 
                                               related_name='critical_calculations')
    is_valid = models.BooleanField(default=True, help_text="Whether the calculation is valid")
    error_message = models.TextField(blank=True, help_text="Error message if calculation failed")
    
    class Meta:
        verbose_name = "Flow Calculation"
        verbose_name_plural = "Flow Calculations"
    
    def __str__(self):
        return f"Calculation for {self.project.name} - {self.calculated_at.strftime('%Y-%m-%d %H:%M')}"