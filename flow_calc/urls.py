"""Flow Calculation URL configuration."""

from django.urls import path
from . import views

app_name = 'flow_calc'

urlpatterns = [
    # Dashboard
    path('', views.FlowDashboardView.as_view(), name='dashboard'),
    
    # Projects
    path('projects/', views.FlowProjectListView.as_view(), name='project_list'),
    path('projects/create/', views.FlowProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/', views.FlowProjectDetailView.as_view(), name='project_detail'),
    path('projects/<int:pk>/edit/', views.FlowProjectUpdateView.as_view(), name='project_update'),
    path('projects/<int:pk>/delete/', views.FlowProjectDeleteView.as_view(), name='project_delete'),
    
    # Steps
    path('projects/<int:project_id>/steps/create/', views.FlowStepCreateView.as_view(), name='step_create'),
    path('projects/<int:project_id>/steps/quick-add/', views.FlowStepQuickAddView.as_view(), name='step_quick_add'),
    path('steps/<int:pk>/edit/', views.FlowStepUpdateView.as_view(), name='step_update'),
    path('steps/<int:pk>/delete/', views.FlowStepDeleteView.as_view(), name='step_delete'),
    
    # Calculations
    path('projects/<int:project_id>/calculate/', views.FlowCalculationView.as_view(), name='calculate'),
    path('api/projects/<int:project_id>/calculate/', views.calculate_flow_api, name='calculate_api'),
]
