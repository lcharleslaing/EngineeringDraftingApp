from django.core.management.base import BaseCommand
from rbac.models import AppAccess, AVAILABLE_APPS

class Command(BaseCommand):
    help = 'Fix app access entries and remove duplicates'

    def handle(self, *args, **options):
        self.stdout.write('Fixing app access entries...')
        
        # Get all current app access entries
        current_entries = AppAccess.objects.all()
        self.stdout.write(f'Found {current_entries.count()} current entries')
        
        # Check for entries with invalid app names
        invalid_entries = current_entries.exclude(app_name__in=[app[0] for app in AVAILABLE_APPS])
        if invalid_entries.exists():
            self.stdout.write(f'Found {invalid_entries.count()} invalid entries:')
            for entry in invalid_entries:
                self.stdout.write(f'  - {entry.app_name}: {entry.description}')
            invalid_entries.delete()
            self.stdout.write('Deleted invalid entries')
        
        # Check for duplicates
        seen_apps = set()
        duplicates = []
        for entry in current_entries:
            if entry.app_name in seen_apps:
                duplicates.append(entry)
            else:
                seen_apps.add(entry.app_name)
        
        if duplicates:
            self.stdout.write(f'Found {len(duplicates)} duplicate entries:')
            for entry in duplicates:
                self.stdout.write(f'  - {entry.app_name}: {entry.description}')
            for entry in duplicates:
                entry.delete()
            self.stdout.write('Deleted duplicate entries')
        
        # Ensure all valid apps have entries
        valid_app_names = [app[0] for app in AVAILABLE_APPS]
        existing_app_names = set(AppAccess.objects.values_list('app_name', flat=True))
        missing_apps = set(valid_app_names) - existing_app_names
        
        if missing_apps:
            self.stdout.write(f'Creating {len(missing_apps)} missing app entries:')
            for app_code in missing_apps:
                app_display = dict(AVAILABLE_APPS)[app_code]
                AppAccess.objects.create(
                    app_name=app_code,
                    description=f'Access to {app_display} functionality',
                    is_enabled=True
                )
                self.stdout.write(f'  - Created: {app_display}')
        
        self.stdout.write(
            self.style.SUCCESS('App access entries fixed successfully!')
        )
