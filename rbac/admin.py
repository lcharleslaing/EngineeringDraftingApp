from django.contrib import admin
from django.utils.html import format_html
from .models import AppAccess, Role, RoleAppPermission, UserRole, AccessLog

@admin.register(AppAccess)
class AppAccessAdmin(admin.ModelAdmin):
    list_display = ('app_name', 'is_enabled', 'description_short', 'created_at')
    list_filter = ('is_enabled', 'created_at')
    search_fields = ('app_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('app_name',)
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'

class RoleAppPermissionInline(admin.TabularInline):
    model = RoleAppPermission
    extra = 0
    fields = ('app_access', 'can_view', 'can_edit', 'can_delete', 'can_admin')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'user_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [RoleAppPermissionInline]
    ordering = ('name',)
    
    def user_count(self, obj):
        count = obj.user_assignments.filter(is_active=True).count()
        return format_html('<span style="color: green;">{}</span>', count)
    user_count.short_description = 'Active Users'

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_active', 'assigned_at', 'assigned_by')
    list_filter = ('is_active', 'role', 'assigned_at')
    search_fields = ('user__username', 'user__email', 'role__name')
    readonly_fields = ('assigned_at',)
    ordering = ('-assigned_at',)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set assigned_by on creation
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'app_name', 'action', 'success', 'ip_address', 'timestamp')
    list_filter = ('success', 'app_name', 'action', 'timestamp')
    search_fields = ('user__username', 'app_name', 'ip_address')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False  # Logs are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs should not be modified
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete logs

# Customize admin site
admin.site.site_header = "Drafting Engineering Flow - RBAC Administration"
admin.site.site_title = "DEF RBAC Admin"
admin.site.index_title = "Role-Based Access Control Management"
