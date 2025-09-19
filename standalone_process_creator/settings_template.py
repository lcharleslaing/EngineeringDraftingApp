# Django settings template for Process Creator
# Copy this to your Django project's settings.py and add the required configurations

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... your existing apps ...
    'process_creator',
]

# Add to MIDDLEWARE (if not already present)
MIDDLEWARE = [
    # ... your existing middleware ...
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Add these settings
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# File conversion tools (optional)
ODA_CONVERTER_PDF = os.getenv('ODA_CONVERTER_PDF')
INVENTOR_IDW_TO_PDF = os.getenv('INVENTOR_IDW_TO_PDF')

# URL configuration
# Add to your main urls.py:
# from django.conf import settings
# from django.conf.urls.static import static
# 
# urlpatterns = [
#     # ... your existing patterns ...
#     path('process-creator/', include('process_creator.urls')),
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
