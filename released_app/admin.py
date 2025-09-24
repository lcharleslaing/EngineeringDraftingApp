from django.contrib import admin
from .models import AppFeature, UserAppPermission


@admin.register(AppFeature)
class AppFeatureAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    search_fields = ("code", "name")
    list_filter = ("is_active",)


@admin.register(UserAppPermission)
class UserAppPermissionAdmin(admin.ModelAdmin):
    list_display = ("user", "app", "access")
    search_fields = ("user__username", "app__code", "app__name")
    list_filter = ("access",)


