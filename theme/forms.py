from django import forms

class ThemeSelectionForm(forms.Form):
    """Form for theme selection"""
    theme = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect(attrs={'class': 'theme-radio'}),
        label="Select Theme"
    )
    
    def __init__(self, available_themes=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if available_themes:
            self.fields['theme'].choices = available_themes
