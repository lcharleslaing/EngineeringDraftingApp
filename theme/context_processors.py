from .models import UserTheme, ThemeSettings

def theme_context(request):
    """Add theme information to template context"""
    context = {}
    
    # Get theme settings
    try:
        theme_settings = ThemeSettings.objects.get(pk=1)
    except ThemeSettings.DoesNotExist:
        theme_settings = ThemeSettings.objects.create()
    
    # Get user's theme
    if request.user.is_authenticated:
        try:
            user_theme = UserTheme.objects.get(user=request.user)
            current_theme = user_theme.theme
        except UserTheme.DoesNotExist:
            current_theme = theme_settings.default_theme
    else:
        current_theme = request.session.get('theme', theme_settings.default_theme)
    
    context.update({
        'current_theme': current_theme,
        'theme_settings': theme_settings,
        'allow_user_themes': theme_settings.allow_user_themes,
    })
    
    return context
