from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home(request):
    """Homepage dashboard view"""
    context = {
        'title': 'Dashboard',
        'user': request.user,
    }
    return render(request, 'main/home.html', context)
