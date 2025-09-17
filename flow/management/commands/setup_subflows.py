from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from flow.models import Flow, FlowStep, SubFlow, SubFlowStep, SubFlowDependency
from datetime import timedelta

class Command(BaseCommand):
    help = 'Creates default subflows for each main flow step'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing subflows before creating new ones',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('Deleting existing subflows...'))
            SubFlowDependency.objects.all().delete()
            SubFlowStep.objects.all().delete()
            SubFlow.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing subflows deleted.'))

        # Get admin user
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.filter(username='admin').first()
            if not admin_user:
                raise Exception("No superuser or 'admin' user found.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error getting admin user: {e}"))
            return

        # Get main flow steps
        flow_steps = FlowStep.objects.filter(is_active=True).order_by('order')
        if not flow_steps.exists():
            self.stdout.write(self.style.ERROR('No active flow steps found. Please run setup_flows first.'))
            return

        self.stdout.write('Creating subflows for each main flow step...')

        # Define subflows for each main step
        subflow_definitions = {
            'approval_prints': {
                'name': 'Print Review Process',
                'description': 'Detailed process for reviewing and approving prints',
                'steps': [
                    {'name': 'Initial Review', 'duration_days': 1, 'description': 'Initial review of print quality and completeness'},
                    {'name': 'Technical Check', 'duration_days': 1, 'description': 'Technical verification of dimensions and specifications'},
                    {'name': 'Approval Decision', 'duration_days': 0.5, 'description': 'Final approval or rejection decision'},
                ]
            },
            'prints_to_customer': {
                'name': 'Customer Delivery Process',
                'description': 'Process for delivering prints to customer',
                'steps': [
                    {'name': 'Package Preparation', 'duration_days': 0.5, 'description': 'Prepare prints for customer delivery'},
                    {'name': 'Quality Check', 'duration_days': 0.5, 'description': 'Final quality check before delivery'},
                    {'name': 'Delivery', 'duration_days': 0.5, 'description': 'Deliver prints to customer'},
                ]
            },
            'long_lead_release': {
                'name': 'Long Lead Procurement Process',
                'description': 'Process for releasing long lead items for procurement',
                'steps': [
                    {'name': 'Item Identification', 'duration_days': 1, 'description': 'Identify all long lead items required'},
                    {'name': 'Vendor Research', 'duration_days': 2, 'description': 'Research and identify potential vendors'},
                    {'name': 'Release Authorization', 'duration_days': 1, 'description': 'Get authorization to release for procurement'},
                    {'name': 'Procurement Release', 'duration_days': 1, 'description': 'Release items to procurement department'},
                ]
            },
            'drafting_queue': {
                'name': 'Drafting Work Process',
                'description': 'Detailed drafting and engineering work process',
                'steps': [
                    {'name': 'Project Setup', 'duration_days': 1, 'description': 'Set up drafting environment and project files'},
                    {'name': 'Initial Drafting', 'duration_days': 5, 'description': 'Create initial drawings and documentation'},
                    {'name': 'Review & Revision', 'duration_days': 3, 'description': 'Internal review and revision of drawings'},
                    {'name': 'Final Documentation', 'duration_days': 2, 'description': 'Finalize all documentation and drawings'},
                    {'name': 'Quality Assurance', 'duration_days': 1, 'description': 'Final quality check of all deliverables'},
                ]
            },
            'engineering_review_and_release': {
                'name': 'Engineering Review Process',
                'description': 'Final engineering review and release process',
                'steps': [
                    {'name': 'Technical Review', 'duration_days': 1, 'description': 'Comprehensive technical review of all work'},
                    {'name': 'Compliance Check', 'duration_days': 1, 'description': 'Verify compliance with standards and regulations'},
                    {'name': 'Final Approval', 'duration_days': 0.5, 'description': 'Final engineering approval and sign-off'},
                    {'name': 'Release Documentation', 'duration_days': 0.5, 'description': 'Prepare and release final documentation'},
                ]
            },
            'release_to_purchasing': {
                'name': 'Purchasing Release Process',
                'description': 'Final release to purchasing department',
                'steps': [
                    {'name': 'Final Verification', 'duration_days': 0.5, 'description': 'Final verification of all requirements'},
                    {'name': 'Purchasing Package', 'duration_days': 0.5, 'description': 'Prepare complete package for purchasing'},
                    {'name': 'Release to Purchasing', 'duration_days': 0.5, 'description': 'Formal release to purchasing department'},
                ]
            },
        }

        for flow_step in flow_steps:
            app_name = flow_step.app_name
            if app_name not in subflow_definitions:
                self.stdout.write(self.style.WARNING(f'  No subflow definition for {app_name}, skipping...'))
                continue

            subflow_data = subflow_definitions[app_name]
            
            # Create subflow
            subflow, created = SubFlow.objects.get_or_create(
                main_flow_step=flow_step,
                defaults={
                    'name': subflow_data['name'],
                    'description': subflow_data['description'],
                    'created_by': admin_user,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created subflow: {subflow.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Subflow already exists: {subflow.name}'))
                continue

            # Create subflow steps
            for i, step_data in enumerate(subflow_data['steps'], 1):
                subflow_step, created = SubFlowStep.objects.get_or_create(
                    subflow=subflow,
                    order=i,
                    defaults={
                        'step_name': step_data['name'],
                        'description': step_data['description'],
                        'estimated_duration': timedelta(days=step_data['duration_days']),
                        'is_required': True,
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'    Created step: {subflow_step.step_name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'    Step already exists: {subflow_step.step_name}'))

            # Create dependencies (sequential finish-to-start)
            subflow_steps = subflow.steps.all().order_by('order')
            for i in range(len(subflow_steps) - 1):
                predecessor = subflow_steps[i]
                successor = subflow_steps[i + 1]
                
                SubFlowDependency.objects.get_or_create(
                    subflow=subflow,
                    predecessor=predecessor,
                    successor=successor,
                    defaults={
                        'dependency_type': 'finish_to_start',
                        'lag_time': timedelta(0),
                        'is_active': True
                    }
                )

        self.stdout.write(self.style.SUCCESS('Subflow setup completed successfully!'))
        self.stdout.write('You can now manage subflows in the Django admin.')
