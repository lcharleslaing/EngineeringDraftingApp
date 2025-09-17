from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def format_duration(duration):
    """Format a timedelta duration for display"""
    if not duration:
        return "N/A"
    
    if isinstance(duration, timedelta):
        total_days = duration.days
        if total_days == 0:
            hours = duration.seconds // 3600
            if hours == 0:
                minutes = duration.seconds // 60
                return f"{minutes}m" if minutes > 0 else "0m"
            return f"{hours}h"
        elif total_days < 7:
            return f"{total_days}d"
        else:
            weeks = total_days // 7
            remaining_days = total_days % 7
            if remaining_days == 0:
                return f"{weeks}w"
            else:
                return f"{weeks}w {remaining_days}d"
    return str(duration)
