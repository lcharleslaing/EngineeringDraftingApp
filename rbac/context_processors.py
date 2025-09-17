from .utils import get_user_accessible_apps, get_user_roles

def rbac_context(request):
    """Add RBAC information to template context"""
    context = {}
    
    if request.user.is_authenticated:
        context.update({
            'user_accessible_apps': get_user_accessible_apps(request.user),
            'user_roles': get_user_roles(request.user),
        })
    else:
        context.update({
            'user_accessible_apps': [],
            'user_roles': [],
        })
    
    return context
