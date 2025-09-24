from django.db import models
from django.conf import settings


class AppFeature(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class UserAppPermission(models.Model):
    VIEW = 'view'
    EDIT = 'edit'
    ADMIN = 'admin'
    ACCESS_LEVELS = [
        (VIEW, 'View'),
        (EDIT, 'Edit'),
        (ADMIN, 'Admin'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    app = models.ForeignKey(AppFeature, on_delete=models.CASCADE)
    access = models.CharField(max_length=20, choices=ACCESS_LEVELS, default=VIEW)

    class Meta:
        unique_together = ('user', 'app')

    def __str__(self) -> str:
        return f"{self.user} - {self.app} ({self.access})"


