from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from flow.models import Flow, FlowStep, SubFlow, SubFlowStep, SubFlowDependency
from datetime import timedelta

class Command(BaseCommand):
    help = 'Creates detailed subflows with realistic durations for each main flow step'

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

        self.stdout.write('Creating detailed subflows with realistic durations...')

        # Define detailed subflows for each main step
        subflow_definitions = {
            'approval_prints': {
                'name': 'Print Review & Approval Process',
                'description': 'Comprehensive process for reviewing, checking, and approving engineering prints',
                'steps': [
                    {'name': 'Initial Print Review', 'duration_hours': 4, 'description': 'Initial review of print quality, completeness, and basic requirements'},
                    {'name': 'Technical Verification', 'duration_hours': 6, 'description': 'Detailed technical verification of dimensions, tolerances, and specifications'},
                    {'name': 'Cross-Reference Check', 'duration_hours': 2, 'description': 'Cross-reference with project specifications and standards'},
                    {'name': 'Quality Assessment', 'duration_hours': 3, 'description': 'Quality assessment and compliance verification'},
                    {'name': 'Approval Decision', 'duration_hours': 1, 'description': 'Final approval or rejection decision with feedback'},
                ]
            },
            'prints_to_customer': {
                'name': 'Customer Delivery Process',
                'description': 'Process for preparing and delivering approved prints to customer',
                'steps': [
                    {'name': 'Print Preparation', 'duration_hours': 2, 'description': 'Prepare prints for customer delivery (formatting, packaging)'},
                    {'name': 'Quality Control Check', 'duration_hours': 1, 'description': 'Final quality control check before customer delivery'},
                    {'name': 'Delivery Coordination', 'duration_hours': 1, 'description': 'Coordinate delivery method and timing with customer'},
                    {'name': 'Customer Delivery', 'duration_hours': 2, 'description': 'Deliver prints to customer and obtain confirmation'},
                ]
            },
            'long_lead_release': {
                'name': 'Long Lead Procurement Process',
                'description': 'Process for identifying and releasing long lead items for procurement',
                'steps': [
                    {'name': 'Item Identification', 'duration_hours': 8, 'description': 'Identify all long lead items from prints and specifications'},
                    {'name': 'Vendor Research', 'duration_hours': 12, 'description': 'Research and identify potential vendors for each item'},
                    {'name': 'Lead Time Analysis', 'duration_hours': 4, 'description': 'Analyze lead times and critical path dependencies'},
                    {'name': 'Release Authorization', 'duration_hours': 2, 'description': 'Get authorization to release items for procurement'},
                    {'name': 'Procurement Package', 'duration_hours': 4, 'description': 'Prepare complete package for procurement department'},
                    {'name': 'Release to Purchasing', 'duration_hours': 1, 'description': 'Formal release to purchasing department'},
                ]
            },
            'drafting_queue': {
                'name': 'Drafting & Engineering Work Process',
                'description': 'Detailed process for drafting and engineering work',
                'steps': [
                    {'name': 'Project Setup', 'duration_hours': 4, 'description': 'Set up drafting environment, project files, and workspace'},
                    {'name': 'Initial Drafting', 'duration_hours': 32, 'description': 'Create initial drawings and technical documentation'},
                    {'name': 'Internal Review', 'duration_hours': 8, 'description': 'Internal review and revision of drawings'},
                    {'name': 'Engineering Calculations', 'duration_hours': 16, 'description': 'Perform engineering calculations and analysis'},
                    {'name': 'Drawing Refinement', 'duration_hours': 12, 'description': 'Refine drawings based on calculations and review'},
                    {'name': 'Documentation Compilation', 'duration_hours': 6, 'description': 'Compile all documentation and drawings'},
                    {'name': 'Quality Assurance', 'duration_hours': 4, 'description': 'Final quality assurance check of all deliverables'},
                ]
            },
            'engineering_review_and_release': {
                'name': 'Engineering Review & Release Process',
                'description': 'Final engineering review and release process',
                'steps': [
                    {'name': 'Technical Review', 'duration_hours': 8, 'description': 'Comprehensive technical review of all engineering work'},
                    {'name': 'Compliance Verification', 'duration_hours': 4, 'description': 'Verify compliance with standards and regulations'},
                    {'name': 'Peer Review', 'duration_hours': 6, 'description': 'Peer review by senior engineer'},
                    {'name': 'Final Approval', 'duration_hours': 2, 'description': 'Final engineering approval and sign-off'},
                    {'name': 'Release Documentation', 'duration_hours': 2, 'description': 'Prepare and release final documentation package'},
                ]
            },
            'release_to_purchasing': {
                'name': 'Purchasing Release Process',
                'description': 'Final release to purchasing department',
                'steps': [
                    {'name': 'Final Verification', 'duration_hours': 2, 'description': 'Final verification of all requirements and specifications'},
                    {'name': 'Purchasing Package Preparation', 'duration_hours': 3, 'description': 'Prepare complete package for purchasing department'},
                    {'name': 'Cost Estimation Review', 'duration_hours': 2, 'description': 'Review cost estimations and budget requirements'},
                    {'name': 'Release Authorization', 'duration_hours': 1, 'description': 'Get final authorization for purchasing release'},
                    {'name': 'Release to Purchasing', 'duration_hours': 1, 'description': 'Formal release to purchasing department'},
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
                # Clear existing steps if resetting
                if options['reset']:
                    subflow.steps.all().delete()
                    subflow.dependencies.all().delete()

            # Create subflow steps
            for i, step_data in enumerate(subflow_data['steps'], 1):
                subflow_step, created = SubFlowStep.objects.get_or_create(
                    subflow=subflow,
                    order=i,
                    defaults={
                        'step_name': step_data['name'],
                        'description': step_data['description'],
                        'estimated_duration': timedelta(hours=step_data['duration_hours']),
                        'is_required': True,
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'    Created step: {subflow_step.step_name} ({subflow_step.estimated_duration})'))
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

        self.stdout.write(self.style.SUCCESS('Detailed subflow setup completed successfully!'))
        self.stdout.write('You can now create projects that will automatically follow these detailed workflows.')
