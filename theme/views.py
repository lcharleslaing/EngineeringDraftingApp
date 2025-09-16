from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import UserTheme, ThemeSettings, THEME_CHOICES
from .forms import ThemeSelectionForm

def theme_selector(request):
    """Theme selection page"""
    # Get or create theme settings
    theme_settings, created = ThemeSettings.objects.get_or_create(pk=1)
    
    # Get user's current theme
    user_theme = None
    if request.user.is_authenticated:
        user_theme, created = UserTheme.objects.get_or_create(
            user=request.user,
            defaults={'theme': theme_settings.default_theme}
        )
    
    # Filter available themes based on settings
    available_themes = [
        choice for choice in THEME_CHOICES 
        if choice[0] in theme_settings.available_themes
    ]
    
    if request.method == 'POST' and theme_settings.allow_user_themes:
        form = ThemeSelectionForm(data=request.POST, available_themes=available_themes)
        if form.is_valid():
            if request.user.is_authenticated:
                user_theme.theme = form.cleaned_data['theme']
                user_theme.save()
                messages.success(request, f'Theme changed to {dict(THEME_CHOICES)[form.cleaned_data["theme"]]}')
            else:
                # Store theme in session for anonymous users
                request.session['theme'] = form.cleaned_data['theme']
                messages.success(request, f'Theme changed to {dict(THEME_CHOICES)[form.cleaned_data["theme"]]}')
            return redirect('theme:selector')
    else:
        initial_theme = user_theme.theme if user_theme else request.session.get('theme', theme_settings.default_theme)
        form = ThemeSelectionForm(available_themes=available_themes, initial={'theme': initial_theme})
    
    context = {
        'form': form,
        'themes': available_themes,
        'current_theme': user_theme.theme if user_theme else request.session.get('theme', theme_settings.default_theme),
        'allow_user_themes': theme_settings.allow_user_themes,
    }
    return render(request, 'theme/theme_selector.html', context)

@require_POST
def change_theme(request):
    """AJAX endpoint to change theme"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    theme = request.POST.get('theme')
    if not theme:
        return JsonResponse({'error': 'Theme not specified'}, status=400)
    
    # Validate theme
    valid_themes = [choice[0] for choice in THEME_CHOICES]
    if theme not in valid_themes:
        return JsonResponse({'error': 'Invalid theme'}, status=400)
    
    # Get or create user theme
    user_theme, created = UserTheme.objects.get_or_create(
        user=request.user,
        defaults={'theme': theme}
    )
    
    if not created:
        user_theme.theme = theme
        user_theme.save()
    
    return JsonResponse({'success': True, 'theme': theme})

def get_user_theme(request):
    """Get user's current theme"""
    if request.user.is_authenticated:
        try:
            user_theme = UserTheme.objects.get(user=request.user)
            return JsonResponse({'theme': user_theme.theme})
        except UserTheme.DoesNotExist:
            pass
    
    # Fallback to session or default
    theme = request.session.get('theme', 'corporate')
    return JsonResponse({'theme': theme})
