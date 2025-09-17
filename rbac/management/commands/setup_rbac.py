from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rbac.models import AppAccess, Role, RoleAppPermission, UserRole, AVAILABLE_APPS

class Command(BaseCommand):
    help = 'Setup RBAC system with default roles and app access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing RBAC data',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Resetting RBAC data...')
            UserRole.objects.all().delete()
            RoleAppPermission.objects.all().delete()
            Role.objects.all().delete()
            AppAccess.objects.all().delete()

        # Create app access entries
        self.stdout.write('Creating app access entries...')
        for app_code, app_name in AVAILABLE_APPS:
            app_access, created = AppAccess.objects.get_or_create(
                app_name=app_code,
                defaults={
                    'description': f'Access to {app_name} functionality',
                    'is_enabled': True
                }
            )
            if created:
                self.stdout.write(f'  Created: {app_name}')
            else:
                self.stdout.write(f'  Exists: {app_name}')

        # Create default roles
        self.stdout.write('Creating default roles...')
        
        # Super Admin Role
        super_admin, created = Role.objects.get_or_create(
            name='Super Admin',
            defaults={
                'description': 'Full system access with all permissions',
                'is_active': True
            }
        )
        if created:
            self.stdout.write('  Created: Super Admin')
        
        # Admin Role
        admin_role, created = Role.objects.get_or_create(
            name='Admin',
            defaults={
                'description': 'Administrative access to most modules',
                'is_active': True
            }
        )
        if created:
            self.stdout.write('  Created: Admin')
        
        # Manager Role
        manager_role, created = Role.objects.get_or_create(
            name='Manager',
            defaults={
                'description': 'Management access to projects and team',
                'is_active': True
            }
        )
        if created:
            self.stdout.write('  Created: Manager')
        
        # User Role
        user_role, created = Role.objects.get_or_create(
            name='User',
            defaults={
                'description': 'Basic user access to core features',
                'is_active': True
            }
        )
        if created:
            self.stdout.write('  Created: User')

        # Set up role permissions
        self.stdout.write('Setting up role permissions...')
        
        # Super Admin gets all permissions
        for app_access in AppAccess.objects.all():
            RoleAppPermission.objects.get_or_create(
                role=super_admin,
                app_access=app_access,
                defaults={
                    'can_view': True,
                    'can_edit': True,
                    'can_delete': True,
                    'can_admin': True
                }
            )
        
        # Admin gets most permissions except some sensitive ones
        admin_apps = ['main', 'theme', 'flow_calc', 'settings', 'account', 'project']
        for app_code in admin_apps:
            try:
                app_access = AppAccess.objects.get(app_name=app_code)
                RoleAppPermission.objects.get_or_create(
                    role=admin_role,
                    app_access=app_access,
                    defaults={
                        'can_view': True,
                        'can_edit': True,
                        'can_delete': True,
                        'can_admin': True
                    }
                )
            except AppAccess.DoesNotExist:
                pass
        
        # Manager gets project and team related permissions
        manager_apps = ['main', 'theme', 'flow_calc', 'project', 'account']
        for app_code in manager_apps:
            try:
                app_access = AppAccess.objects.get(app_name=app_code)
                RoleAppPermission.objects.get_or_create(
                    role=manager_role,
                    app_access=app_access,
                    defaults={
                        'can_view': True,
                        'can_edit': True,
                        'can_delete': False,
                        'can_admin': False
                    }
                )
            except AppAccess.DoesNotExist:
                pass
        
        # User gets basic permissions
        user_apps = ['main', 'theme', 'flow_calc']
        for app_code in user_apps:
            try:
                app_access = AppAccess.objects.get(app_name=app_code)
                RoleAppPermission.objects.get_or_create(
                    role=user_role,
                    app_access=app_access,
                    defaults={
                        'can_view': True,
                        'can_edit': False,
                        'can_delete': False,
                        'can_admin': False
                    }
                )
            except AppAccess.DoesNotExist:
                pass

        # Assign super admin role to superusers
        self.stdout.write('Assigning roles to superusers...')
        superusers = User.objects.filter(is_superuser=True)
        for user in superusers:
            UserRole.objects.get_or_create(
                user=user,
                role=super_admin,
                defaults={'is_active': True}
            )
            self.stdout.write(f'  Assigned Super Admin to: {user.username}')

        self.stdout.write(
            self.style.SUCCESS('RBAC setup completed successfully!')
        )
        self.stdout.write('You can now manage roles and permissions in the Django admin.')
