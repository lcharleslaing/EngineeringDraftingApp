from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Register your models here.

# Customize the admin site
admin.site.site_header = "Drafting Engineering Flow Administration"
admin.site.site_title = "DEF Admin"
admin.site.index_title = "Welcome to DEF Administration"

# Ensure User model is properly registered (it should be by default)
# But we can customize it if needed
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)

# Re-register User with custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
