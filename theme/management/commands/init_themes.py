from django.core.management.base import BaseCommand
from theme.models import ThemeSettings, THEME_CHOICES

class Command(BaseCommand):
    help = 'Initialize theme settings with all available themes'

    def handle(self, *args, **options):
        # Create or update theme settings
        theme_settings, created = ThemeSettings.objects.get_or_create(
            pk=1,
            defaults={
                'default_theme': 'corporate',
                'allow_user_themes': True,
                'available_themes': [choice[0] for choice in THEME_CHOICES]
            }
        )
        
        if not created:
            # Update existing settings to include all themes
            theme_settings.available_themes = [choice[0] for choice in THEME_CHOICES]
            theme_settings.save()
            self.stdout.write(
                self.style.SUCCESS('Theme settings updated with all available themes')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Theme settings created with all available themes')
            )
        
        self.stdout.write(f'Available themes: {len(THEME_CHOICES)}')
        self.stdout.write(f'Default theme: {theme_settings.default_theme}')
        self.stdout.write(f'User themes enabled: {theme_settings.allow_user_themes}')
