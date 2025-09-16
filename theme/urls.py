from django.urls import path
from . import views

app_name = 'theme'

urlpatterns = [
    path('', views.theme_selector, name='selector'),
    path('change/', views.change_theme, name='change'),
    path('get/', views.get_user_theme, name='get'),
]
