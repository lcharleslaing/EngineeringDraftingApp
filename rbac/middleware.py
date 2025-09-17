from django.http import HttpResponseForbidden, Http404
from django.shortcuts import render
from django.urls import resolve, Resolver404
from django.contrib import messages
from .utils import is_app_enabled, has_app_access, log_access_attempt
import logging

logger = logging.getLogger(__name__)

class RBACMiddleware:
    """
    Middleware to automatically check app access based on URL patterns
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Map URL patterns to app names
        self.app_url_mapping = {
            'main:': 'main',
            'theme:': 'theme',
            'settings:': 'settings',
            'account:': 'account',
            'project:': 'project',
            'approval_prints:': 'approval_prints',
            'product_configuration:': 'product_configuration',
        }
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Process view before it's called
        """
        try:
            # Get the resolved URL name
            resolver_match = resolve(request.path_info)
            url_name = resolver_match.url_name
            
            # Skip admin URLs and static files
            if url_name and (
                url_name.startswith('admin:') or 
                url_name.startswith('static:') or
                url_name.startswith('media:')
            ):
                return None
            
            # Determine app name from URL
            app_name = self._get_app_name_from_url(request.path_info, url_name)
            
            if app_name:
                # Check if app is enabled
                if not is_app_enabled(app_name):
                    logger.warning(f"Access to disabled app {app_name} attempted by {request.user}")
                    messages.error(request, f"The {app_name} module is currently disabled.")
                    return render(request, 'rbac/access_denied.html', {
                        'app_name': app_name,
                        'reason': 'disabled'
                    }, status=404)
                
                # Check user access
                if not has_app_access(request.user, app_name, 'view'):
                    logger.warning(f"Access denied to {app_name} for user {request.user}")
                    messages.error(request, f"You don't have permission to access {app_name}.")
                    return render(request, 'rbac/access_denied.html', {
                        'app_name': app_name,
                        'reason': 'permission_denied'
                    }, status=403)
                
                # Log successful access
                log_access_attempt(request.user, app_name, 'view', success=True, request=request)
        
        except Resolver404:
            # URL not found, let Django handle it
            pass
        except Exception as e:
            logger.error(f"Error in RBAC middleware: {e}")
        
        return None
    
    def _get_app_name_from_url(self, path, url_name):
        """
        Determine app name from URL path or name
        """
        # Check URL patterns first
        if url_name:
            for pattern, app in self.app_url_mapping.items():
                if url_name.startswith(pattern):
                    return app
        
        # Fallback to path-based detection
        path_parts = path.strip('/').split('/')
        if path_parts:
            first_part = path_parts[0]
            if first_part in [app[0] for app in self.app_url_mapping.values()]:
                return first_part
        
        return None
