from functools import wraps
from django.http import HttpResponseForbidden, Http404
from django.shortcuts import render
from django.contrib import messages
from .utils import check_app_access, has_app_access, log_access_attempt, is_app_enabled
from django.core.exceptions import PermissionDenied

def require_app_access(app_name, action='view'):
    """
    Decorator to require access to a specific app
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if app is enabled
            if not is_app_enabled(app_name):
                messages.error(request, f"The {app_name} module is currently disabled.")
                return render(request, 'rbac/access_denied.html', {
                    'app_name': app_name,
                    'reason': 'disabled'
                }, status=404)
            
            # Check user access
            try:
                check_app_access(request.user, app_name, action)
                # Log successful access
                log_access_attempt(request.user, app_name, action, success=True, request=request)
            except PermissionDenied:
                messages.error(request, f"You don't have permission to access {app_name}.")
                return render(request, 'rbac/access_denied.html', {
                    'app_name': app_name,
                    'reason': 'permission_denied'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_role(role_name):
    """
    Decorator to require a specific role
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "You must be logged in to access this page.")
                return render(request, 'rbac/access_denied.html', {
                    'reason': 'not_authenticated'
                }, status=401)
            
            user_roles = [ur.role.name for ur in request.user.user_roles.filter(is_active=True)]
            
            if role_name not in user_roles and not request.user.is_superuser:
                messages.error(request, f"You need the {role_name} role to access this page.")
                return render(request, 'rbac/access_denied.html', {
                    'role_name': role_name,
                    'reason': 'role_required'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_any_role(*role_names):
    """
    Decorator to require any of the specified roles
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "You must be logged in to access this page.")
                return render(request, 'rbac/access_denied.html', {
                    'reason': 'not_authenticated'
                }, status=401)
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            user_roles = [ur.role.name for ur in request.user.user_roles.filter(is_active=True)]
            
            if not any(role in user_roles for role in role_names):
                messages.error(request, f"You need one of these roles to access this page: {', '.join(role_names)}")
                return render(request, 'rbac/access_denied.html', {
                    'role_names': role_names,
                    'reason': 'role_required'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
