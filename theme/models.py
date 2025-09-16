from django.db import models
from django.contrib.auth.models import User

# DaisyUI Theme Choices
THEME_CHOICES = [
    ('light', 'Light'),
    ('dark', 'Dark'),
    ('cupcake', 'Cupcake'),
    ('bumblebee', 'Bumblebee'),
    ('emerald', 'Emerald'),
    ('corporate', 'Corporate'),
    ('synthwave', 'Synthwave'),
    ('retro', 'Retro'),
    ('cyberpunk', 'Cyberpunk'),
    ('valentine', 'Valentine'),
    ('halloween', 'Halloween'),
    ('garden', 'Garden'),
    ('forest', 'Forest'),
    ('aqua', 'Aqua'),
    ('lofi', 'Lofi'),
    ('pastel', 'Pastel'),
    ('fantasy', 'Fantasy'),
    ('wireframe', 'Wireframe'),
    ('black', 'Black'),
    ('luxury', 'Luxury'),
    ('dracula', 'Dracula'),
    ('cmyk', 'CMYK'),
    ('autumn', 'Autumn'),
    ('business', 'Business'),
    ('acid', 'Acid'),
    ('lemonade', 'Lemonade'),
    ('night', 'Night'),
    ('coffee', 'Coffee'),
    ('winter', 'Winter'),
    ('dim', 'Dim'),
    ('nord', 'Nord'),
    ('sunset', 'Sunset'),
]

class UserTheme(models.Model):
    """Model to store user's theme preference"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='theme_preference')
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='corporate')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Theme"
        verbose_name_plural = "User Themes"
    
    def __str__(self):
        return f"{self.user.username} - {self.theme}"

class ThemeSettings(models.Model):
    """Global theme settings"""
    allow_user_themes = models.BooleanField(default=True, help_text="Allow users to change their theme")
    default_theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='corporate')
    available_themes = models.JSONField(default=list, help_text="List of available themes for users")
    
    class Meta:
        verbose_name = "Theme Settings"
        verbose_name_plural = "Theme Settings"
    
    def __str__(self):
        return f"Theme Settings - Default: {self.default_theme}"
    
    def save(self, *args, **kwargs):
        if not self.available_themes:
            self.available_themes = [choice[0] for choice in THEME_CHOICES]
        super().save(*args, **kwargs)
