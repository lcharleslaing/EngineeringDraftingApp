"""Flow Calculation forms."""

from django import forms
from django.contrib.auth.models import User
from .models import FlowProject, FlowStep


class FlowProjectForm(forms.ModelForm):
    """Form for creating and editing flow projects."""
    
    class Meta:
        model = FlowProject
        fields = ['name', 'description', 'start_date', 'duration_days']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'textarea textarea-bordered w-full'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
            'duration_days': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'min': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # No crispy forms layout needed - using custom templates
    
    def save(self, commit=True):
        project = super().save(commit=False)
        if self.user:
            project.created_by = self.user
        if commit:
            project.save()
        return project


class FlowStepForm(forms.ModelForm):
    """Form for creating and editing flow steps."""
    
    class Meta:
        model = FlowStep
        fields = ['name', 'description', 'duration_days', 'dependencies']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'textarea textarea-bordered w-full'}),
            'duration_days': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'min': '1'}),
            'dependencies': forms.CheckboxSelectMultiple(attrs={'class': 'checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # Filter dependencies to only show steps from the same project
        if self.project:
            self.fields['dependencies'].queryset = FlowStep.objects.filter(project=self.project)
        
        # No crispy forms layout needed - using custom templates
    
    def clean(self):
        cleaned_data = super().clean()
        dependencies = cleaned_data.get('dependencies')
        
        # Check for circular dependencies
        if self.instance.pk and dependencies:
            for dep in dependencies:
                if self.instance in dep.dependencies.all():
                    raise forms.ValidationError("Circular dependency detected.")
        
        return cleaned_data
    
    def save(self, commit=True):
        step = super().save(commit=False)
        if self.project:
            step.project = self.project
        if commit:
            step.save()
        return step


class FlowStepQuickAddForm(forms.Form):
    """Quick add form for multiple steps at once."""
    
    step_data = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 10,
            'class': 'textarea textarea-bordered w-full font-mono text-sm',
            'placeholder': 'Enter steps one per line in format: Name|Duration|Dependencies\nExample:\nDesign|5|\nDevelopment|10|Design\nTesting|3|Development'
        }),
        help_text="Enter steps one per line. Format: Name|Duration|Dependencies (comma-separated step names)"
    )
    
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # No crispy forms layout needed - using custom templates
    
    def clean_step_data(self):
        data = self.cleaned_data['step_data']
        lines = [line.strip() for line in data.split('\n') if line.strip()]
        
        if not lines:
            raise forms.ValidationError("Please enter at least one step.")
        
        steps = []
        for i, line in enumerate(lines, 1):
            parts = line.split('|')
            if len(parts) < 2:
                raise forms.ValidationError(f"Line {i}: Invalid format. Use: Name|Duration|Dependencies")
            
            name = parts[0].strip()
            if not name:
                raise forms.ValidationError(f"Line {i}: Step name is required.")
            
            try:
                duration = int(parts[1].strip())
                if duration <= 0:
                    raise forms.ValidationError(f"Line {i}: Duration must be positive.")
            except ValueError:
                raise forms.ValidationError(f"Line {i}: Duration must be a number.")
            
            dependencies = []
            if len(parts) > 2 and parts[2].strip():
                dep_names = [dep.strip() for dep in parts[2].split(',') if dep.strip()]
                dependencies = dep_names
            
            steps.append({
                'name': name,
                'duration': duration,
                'dependencies': dependencies
            })
        
        return steps
    
    def save(self, commit=True):
        if not self.project:
            return []
        
        steps_data = self.cleaned_data['step_data']
        created_steps = []
        
        for step_data in steps_data:
            # Find dependency steps by name
            dependency_steps = []
            for dep_name in step_data['dependencies']:
                try:
                    dep_step = FlowStep.objects.get(project=self.project, name=dep_name)
                    dependency_steps.append(dep_step)
                except FlowStep.DoesNotExist:
                    # Skip invalid dependency names
                    continue
            
            # Create the step
            step = FlowStep.objects.create(
                project=self.project,
                name=step_data['name'],
                duration_days=step_data['duration']
            )
            
            # Add dependencies
            if dependency_steps:
                step.dependencies.set(dependency_steps)
            
            created_steps.append(step)
        
        return created_steps


class FlowCalculationForm(forms.Form):
    """Form for triggering flow calculations."""
    
    recalculate = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Recalculate all dates and dependencies"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # No crispy forms layout needed - using custom templates
