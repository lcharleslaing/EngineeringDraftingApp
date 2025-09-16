from django.contrib import admin
from .models import UserTheme, ThemeSettings

@admin.register(UserTheme)
class UserThemeAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'created_at', 'updated_at')
    list_filter = ('theme', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)

@admin.register(ThemeSettings)
class ThemeSettingsAdmin(admin.ModelAdmin):
    list_display = ('default_theme', 'allow_user_themes', 'available_themes_count')
    fields = ('default_theme', 'allow_user_themes', 'available_themes')
    
    def available_themes_count(self, obj):
        return len(obj.available_themes) if obj.available_themes else 0
    available_themes_count.short_description = 'Available Themes Count'
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not ThemeSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
