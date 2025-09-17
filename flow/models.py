from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import uuid

class FlowCategory(models.Model):
    """Categories for different types of flows"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Hex color code")
    icon = models.CharField(max_length=50, default='fas fa-project-diagram', help_text="FontAwesome icon class")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Flow Category"
        verbose_name_plural = "Flow Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Flow(models.Model):
    """Main flow definition"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(FlowCategory, on_delete=models.CASCADE, related_name='flows')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_flows')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Flow"
        verbose_name_plural = "Flows"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class FlowStep(models.Model):
    """Individual steps in a flow"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled'),
    ]
    
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, related_name='steps')
    app_name = models.CharField(max_length=50, help_text="Django app name")
    step_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(help_text="Order in the flow (1, 2, 3...)")
    estimated_duration = models.DurationField(help_text="Estimated time to complete")
    is_required = models.BooleanField(default=True, help_text="Must this step be completed?")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Flow Step"
        verbose_name_plural = "Flow Steps"
        ordering = ['flow', 'order']
        unique_together = ['flow', 'order']
    
    def __str__(self):
        return f"{self.flow.name} - {self.step_name}"
    
    def clean(self):
        if self.estimated_duration and self.estimated_duration <= timedelta(0):
            raise ValidationError("Estimated duration must be positive")

class FlowDependency(models.Model):
    """Dependencies between flow steps"""
    DEPENDENCY_TYPES = [
        ('finish_to_start', 'Finish to Start'),
        ('start_to_start', 'Start to Start'),
        ('finish_to_finish', 'Finish to Finish'),
        ('start_to_finish', 'Start to Finish'),
    ]
    
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, related_name='dependencies')
    predecessor = models.ForeignKey(FlowStep, on_delete=models.CASCADE, related_name='successors')
    successor = models.ForeignKey(FlowStep, on_delete=models.CASCADE, related_name='predecessors')
    dependency_type = models.CharField(max_length=20, choices=DEPENDENCY_TYPES, default='finish_to_start')
    lag_time = models.DurationField(default=timedelta(0), help_text="Time delay between steps")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Flow Dependency"
        verbose_name_plural = "Flow Dependencies"
        unique_together = ['predecessor', 'successor']
    
    def __str__(self):
        return f"{self.predecessor.step_name} → {self.successor.step_name}"
    
    def clean(self):
        if self.predecessor == self.successor:
            raise ValidationError("A step cannot depend on itself")
        if self.predecessor.flow != self.successor.flow:
            raise ValidationError("Dependencies must be within the same flow")

class Project(models.Model):
    """Individual project instances that follow flows"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, related_name='projects')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_projects')
    start_date = models.DateTimeField(null=True, blank=True)
    target_completion_date = models.DateTimeField(null=True, blank=True)
    actual_completion_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.flow.name})"
    
    @property
    def is_overdue(self):
        if self.target_completion_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.target_completion_date
        return False
    
    @property
    def progress_percentage(self):
        completed_steps = self.project_steps.filter(status='completed').count()
        total_steps = self.project_steps.count()
        if total_steps == 0:
            return 0
        return (completed_steps / total_steps) * 100

class ProjectStep(models.Model):
    """Individual step instances for projects"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_steps')
    flow_step = models.ForeignKey(FlowStep, on_delete=models.CASCADE, related_name='project_instances')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_steps')
    start_date = models.DateTimeField(null=True, blank=True)
    target_completion_date = models.DateTimeField(null=True, blank=True)
    actual_completion_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Project Step"
        verbose_name_plural = "Project Steps"
        ordering = ['flow_step__order']
        unique_together = ['project', 'flow_step']
    
    def __str__(self):
        return f"{self.project.name} - {self.flow_step.step_name}"
    
    @property
    def is_overdue(self):
        if self.target_completion_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.target_completion_date
        return False
    
    @property
    def can_start(self):
        """Check if this step can start based on dependencies"""
        if self.status != 'pending':
            return False
        
        # Check if all predecessor steps are completed
        dependencies = FlowDependency.objects.filter(
            successor=self.flow_step,
            is_active=True
        )
        
        for dep in dependencies:
            try:
                pred_step = ProjectStep.objects.get(
                    project=self.project,
                    flow_step=dep.predecessor
                )
                if pred_step.status != 'completed':
                    return False
            except ProjectStep.DoesNotExist:
                return False
        
        return True

class SubFlow(models.Model):
    """Sub-flows within main flow steps"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    main_flow_step = models.ForeignKey(FlowStep, on_delete=models.CASCADE, related_name='subflows')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_subflows')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sub Flow"
        verbose_name_plural = "Sub Flows"
        ordering = ['main_flow_step', 'name']

    def __str__(self):
        return f"{self.main_flow_step.step_name} - {self.name}"

class SubFlowStep(models.Model):
    """Individual steps within a subflow"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled'),
    ]

    subflow = models.ForeignKey(SubFlow, on_delete=models.CASCADE, related_name='steps')
    step_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(help_text="Order in the subflow (1, 2, 3...)")
    estimated_duration = models.DurationField(help_text="Estimated time to complete")
    is_required = models.BooleanField(default=True, help_text="Must this step be completed?")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sub Flow Step"
        verbose_name_plural = "Sub Flow Steps"
        ordering = ['subflow', 'order']
        unique_together = ['subflow', 'order']

    def __str__(self):
        return f"{self.subflow.name} - {self.step_name}"

    def clean(self):
        if self.estimated_duration and self.estimated_duration <= timedelta(0):
            raise ValidationError("Estimated duration must be positive")

class SubFlowDependency(models.Model):
    """Dependencies between subflow steps"""
    DEPENDENCY_TYPES = [
        ('finish_to_start', 'Finish to Start'),
        ('start_to_start', 'Start to Start'),
        ('finish_to_finish', 'Finish to Finish'),
        ('start_to_finish', 'Start to Finish'),
    ]

    subflow = models.ForeignKey(SubFlow, on_delete=models.CASCADE, related_name='dependencies')
    predecessor = models.ForeignKey(SubFlowStep, on_delete=models.CASCADE, related_name='successors')
    successor = models.ForeignKey(SubFlowStep, on_delete=models.CASCADE, related_name='predecessors')
    dependency_type = models.CharField(max_length=20, choices=DEPENDENCY_TYPES, default='finish_to_start')
    lag_time = models.DurationField(default=timedelta(0), help_text="Time delay between steps")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sub Flow Dependency"
        verbose_name_plural = "Sub Flow Dependencies"
        unique_together = ['predecessor', 'successor']

    def __str__(self):
        return f"{self.predecessor.step_name} → {self.successor.step_name}"

    def clean(self):
        if self.predecessor == self.successor:
            raise ValidationError("A step cannot depend on itself")
        if self.predecessor.subflow != self.successor.subflow:
            raise ValidationError("Dependencies must be within the same subflow")

class ProjectSubFlowStep(models.Model):
    """Individual subflow step instances for projects"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='subflow_steps')
    subflow_step = models.ForeignKey(SubFlowStep, on_delete=models.CASCADE, related_name='project_instances')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_subflow_steps')
    start_date = models.DateTimeField(null=True, blank=True)
    target_completion_date = models.DateTimeField(null=True, blank=True)
    actual_completion_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Project Sub Flow Step"
        verbose_name_plural = "Project Sub Flow Steps"
        ordering = ['subflow_step__order']
        unique_together = ['project', 'subflow_step']

    def __str__(self):
        return f"{self.project.name} - {self.subflow_step.step_name}"

    @property
    def is_overdue(self):
        if self.target_completion_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.target_completion_date
        return False

    @property
    def can_start(self):
        """Check if this subflow step can start based on dependencies"""
        if self.status != 'pending':
            return False

        # Check if all predecessor steps are completed
        dependencies = SubFlowDependency.objects.filter(
            successor=self.subflow_step,
            is_active=True
        )

        for dep in dependencies:
            try:
                pred_step = ProjectSubFlowStep.objects.get(
                    project=self.project,
                    subflow_step=dep.predecessor
                )
                if pred_step.status != 'completed':
                    return False
            except ProjectSubFlowStep.DoesNotExist:
                return False

        return True

class FlowTemplate(models.Model):
    """Templates for common flows"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(FlowCategory, on_delete=models.CASCADE, related_name='templates')
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Flow Template"
        verbose_name_plural = "Flow Templates"
        ordering = ['name']

    def __str__(self):
        return self.name
