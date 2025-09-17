from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404
from .models import AppAccess, UserRole, AccessLog
import logging

logger = logging.getLogger(__name__)

def has_app_access(user, app_name, action='view'):
    """
    Check if user has access to a specific app with given action
    """
    if not user or not user.is_authenticated:
        return False
    
    # Check if app is enabled
    try:
        app_access = AppAccess.objects.get(app_name=app_name)
        if not app_access.is_enabled:
            return False
    except AppAccess.DoesNotExist:
        return False
    
    # Superusers have access to everything
    if user.is_superuser:
        return True
    
    # Check user roles
    user_roles = UserRole.objects.filter(user=user, is_active=True).select_related('role')
    
    for user_role in user_roles:
        role_permissions = user_role.role.roleapppermission_set.filter(
            app_access=app_access,
            role=user_role.role
        ).first()
        
        if role_permissions:
            if action == 'view' and role_permissions.can_view:
                return True
            elif action == 'edit' and role_permissions.can_edit:
                return True
            elif action == 'delete' and role_permissions.can_delete:
                return True
            elif action == 'admin' and role_permissions.can_admin:
                return True
    
    return False

def check_app_access(user, app_name, action='view'):
    """
    Check app access and raise appropriate exceptions
    """
    if not has_app_access(user, app_name, action):
        # Log the access attempt
        log_access_attempt(user, app_name, action, success=False, 
                          error_message=f"Access denied for {action} on {app_name}")
        raise PermissionDenied(f"You don't have permission to {action} {app_name}")

def get_user_accessible_apps(user):
    """
    Get list of apps accessible to user
    """
    if not user or not user.is_authenticated:
        return []
    
    if user.is_superuser:
        return AppAccess.objects.filter(is_enabled=True).values_list('app_name', flat=True)
    
    accessible_apps = set()
    user_roles = UserRole.objects.filter(user=user, is_active=True).select_related('role')
    
    for user_role in user_roles:
        role_permissions = user_role.role.roleapppermission_set.filter(
            can_view=True
        ).select_related('app_access')
        
        for permission in role_permissions:
            if permission.app_access.is_enabled:
                accessible_apps.add(permission.app_access.app_name)
    
    return list(accessible_apps)

def log_access_attempt(user, app_name, action, success=True, error_message='', request=None):
    """
    Log access attempts for auditing
    """
    try:
        AccessLog.objects.create(
            user=user if user.is_authenticated else None,
            app_name=app_name,
            action=action,
            ip_address=request.META.get('REMOTE_ADDR') if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
            success=success,
            error_message=error_message
        )
    except Exception as e:
        logger.error(f"Failed to log access attempt: {e}")

def get_user_roles(user):
    """
    Get all active roles for a user
    """
    if not user or not user.is_authenticated:
        return []
    
    return UserRole.objects.filter(user=user, is_active=True).select_related('role')

def is_app_enabled(app_name):
    """
    Check if an app is enabled in the system
    """
    try:
        app_access = AppAccess.objects.get(app_name=app_name)
        return app_access.is_enabled
    except AppAccess.DoesNotExist:
        return False
