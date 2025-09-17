from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

# Available apps in the system
AVAILABLE_APPS = [
    ('main', 'Main Dashboard'),
    ('theme', 'Theme Management'),
    ('flow_calc', 'Flow Calculator'),
    ('settings', 'Settings'),
    ('account', 'Account Management'),
    ('project', 'Project Management'),
    ('approval_prints', 'Approval Prints'),
    ('product_configuration', 'Product Configuration'),
    ('user_messages', 'Messages'),
    ('suggestions', 'Suggestions'),
    ('prints_to_customer', 'Prints to Customer'),
    ('long_lead_release', 'Long Lead Release'),
    ('drafting_queue', 'Drafting Queue'),
    ('engineering_review_and_release', 'Engineering Review and Release'),
    ('release_to_purchasing', 'Release to Purchasing'),
    ('process_creator', 'Process Creator'),
]

class AppAccess(models.Model):
    """Model to control which apps are accessible"""
    app_name = models.CharField(max_length=50, choices=AVAILABLE_APPS, unique=True)
    is_enabled = models.BooleanField(default=True, help_text="Enable/disable this app")
    description = models.TextField(blank=True, help_text="Description of what this app does")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "App Access"
        verbose_name_plural = "App Access Control"
        ordering = ['app_name']
    
    def __str__(self):
        status = "Enabled" if self.is_enabled else "Disabled"
        return f"{self.get_app_name_display()} - {status}"

class Role(models.Model):
    """Custom roles for users"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Many-to-many relationship with apps
    allowed_apps = models.ManyToManyField(
        AppAccess, 
        through='RoleAppPermission',
        related_name='roles'
    )
    
    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class RoleAppPermission(models.Model):
    """Through model for role-app permissions"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    app_access = models.ForeignKey(AppAccess, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['role', 'app_access']
        verbose_name = "Role App Permission"
        verbose_name_plural = "Role App Permissions"
    
    def __str__(self):
        return f"{self.role.name} - {self.app_access.get_app_name_display()}"

class UserRole(models.Model):
    """Assign roles to users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_roles'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'role']
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

class AccessLog(models.Model):
    """Log access attempts for auditing"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    app_name = models.CharField(max_length=50)
    action = models.CharField(max_length=50)  # view, edit, delete, admin
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Access Log"
        verbose_name_plural = "Access Logs"
        ordering = ['-timestamp']
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.user.username if self.user else 'Anonymous'} - {self.app_name} - {status}"
