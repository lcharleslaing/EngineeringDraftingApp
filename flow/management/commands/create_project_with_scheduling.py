from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from flow.models import Flow, FlowStep, Project, ProjectStep, SubFlow, SubFlowStep, ProjectSubFlowStep
from datetime import timedelta

class Command(BaseCommand):
    help = 'Creates a new project with automatic scheduling based on flow durations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='Name of the project to create',
        )
        parser.add_argument(
            '--description',
            type=str,
            default='',
            help='Description of the project',
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format (defaults to today)',
        )
        parser.add_argument(
            '--assigned-to',
            type=str,
            help='Username to assign the project to',
        )

    def handle(self, *args, **options):
        project_name = options['name']
        project_description = options['description']
        
        # Parse start date
        if options['start_date']:
            try:
                start_date = timezone.datetime.strptime(options['start_date'], '%Y-%m-%d').date()
                start_datetime = timezone.datetime.combine(start_date, timezone.datetime.min.time())
                start_datetime = timezone.make_aware(start_datetime)
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD'))
                return
        else:
            start_datetime = timezone.now()
        
        # Get assigned user
        assigned_user = None
        if options['assigned_to']:
            try:
                assigned_user = User.objects.get(username=options['assigned_to'])
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User "{options["assigned_to"]}" not found'))
                return
        
        # Get the main flow
        try:
            flow = Flow.objects.filter(is_active=True).first()
            if not flow:
                self.stdout.write(self.style.ERROR('No active flow found. Please run setup_flows first.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting flow: {e}'))
            return

        # Get flow steps in order
        flow_steps = FlowStep.objects.filter(flow=flow, is_active=True).order_by('order')
        if not flow_steps.exists():
            self.stdout.write(self.style.ERROR('No flow steps found.'))
            return

        # Create the project
        project = Project.objects.create(
            name=project_name,
            description=project_description,
            flow=flow,
            created_by=User.objects.filter(is_superuser=True).first(),
            assigned_to=assigned_user,
            status='not_started',
            start_date=start_datetime
        )

        self.stdout.write(self.style.SUCCESS(f'Created project: {project.name}'))

        # Calculate scheduling
        current_date = start_datetime
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

            self.stdout.write(f'  Created main step: {flow_step.step_name} (Due: {target_completion.strftime("%Y-%m-%d %H:%M")})')

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

                    self.stdout.write(f'    Created sub-step: {subflow_step.step_name} (Due: {subflow_target_completion.strftime("%Y-%m-%d %H:%M")})')
                    
                    # Move to next subflow step (finish-to-start dependency)
                    subflow_current_date = subflow_target_completion

            # Move to next main step (finish-to-start dependency)
            current_date = target_completion

        # Set project target completion date
        project.target_completion_date = start_datetime + total_duration
        project.save()

        self.stdout.write(self.style.SUCCESS(f'Project scheduled from {start_datetime.strftime("%Y-%m-%d")} to {project.target_completion_date.strftime("%Y-%m-%d")}'))
        self.stdout.write(f'Total estimated duration: {total_duration.days} days, {total_duration.seconds // 3600} hours')
        self.stdout.write(f'Project ID: {project.id}')
        self.stdout.write('You can now view this project in the workflow steps on the homepage.')
