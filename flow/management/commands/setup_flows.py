from django.core.management.base import BaseCommand
from flow.utils import create_default_engineering_flow

class Command(BaseCommand):
    help = 'Setup default engineering flow with all required steps'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing flow data',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Resetting flow data...')
            from flow.models import Flow, FlowStep, FlowDependency, FlowCategory
            FlowDependency.objects.all().delete()
            FlowStep.objects.all().delete()
            Flow.objects.all().delete()
            FlowCategory.objects.all().delete()

        self.stdout.write('Creating default engineering flow...')
        flow = create_default_engineering_flow()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created flow: {flow.name}')
        )
        self.stdout.write(f'Flow has {flow.steps.count()} steps')
        self.stdout.write(f'Flow has {flow.dependencies.count()} dependencies')
        
        # List all steps
        self.stdout.write('\nFlow Steps:')
        for step in flow.steps.all().order_by('order'):
            self.stdout.write(f'  {step.order}. {step.step_name} ({step.app_name}) - {step.estimated_duration}')
        
        self.stdout.write('\nDependencies:')
        for dep in flow.dependencies.all():
            self.stdout.write(f'  {dep.predecessor.step_name} → {dep.successor.step_name}')
        
        self.stdout.write(
            self.style.SUCCESS('\nFlow setup completed successfully!')
        )
