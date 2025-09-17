from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from flow.models import Flow, FlowStep, Project, ProjectStep
from datetime import timedelta
import uuid

class Command(BaseCommand):
    help = 'Creates sample projects for testing the workflow system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of sample projects to create',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created test user: testuser'))
        
        # Get the main flow
        try:
            flow = Flow.objects.filter(is_active=True).first()
            if not flow:
                self.stdout.write(self.style.ERROR('No active flow found. Please run setup_flow first.'))
                return
        except Flow.DoesNotExist:
            self.stdout.write(self.style.ERROR('No flow found. Please run setup_flow first.'))
            return
        
        # Get flow steps
        flow_steps = FlowStep.objects.filter(flow=flow, is_active=True).order_by('order')
        if not flow_steps.exists():
            self.stdout.write(self.style.ERROR('No flow steps found. Please run setup_flow first.'))
            return
        
        self.stdout.write(f'Creating {count} sample projects...')
        
        for i in range(count):
            # Create project
            project = Project.objects.create(
                name=f'Sample Project {i+1}',
                description=f'This is a sample project for testing the {flow.name} workflow.',
                flow=flow,
                created_by=user,
                status='not_started'
            )
            
            # Create project steps
            for flow_step in flow_steps:
                ProjectStep.objects.create(
                    project=project,
                    flow_step=flow_step,
                    status='pending'
                )
            
            self.stdout.write(self.style.SUCCESS(f'  Created: {project.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} sample projects!'))
        self.stdout.write('You can now view them in the workflow steps on the homepage.')
