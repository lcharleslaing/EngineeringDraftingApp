from django.urls import path
from . import views

app_name = 'flow'

urlpatterns = [
    path('step/<str:app_name>/', views.step_detail, name='step_detail'),
    path('step-detail/<str:app_name>/', views.step_detail_page, name='step_detail_page'),
    path('project/<uuid:project_id>/', views.project_detail, name='project_detail'),
    path('create-project/', views.create_new_project, name='create_project'),
    path('start-step/<int:project_step_id>/', views.start_project_step, name='start_project_step'),
    path('complete-step/<int:project_step_id>/', views.complete_project_step, name='complete_project_step'),
    path('block-step/<int:project_step_id>/', views.block_project_step, name='block_project_step'),
    path('unblock-step/<int:project_step_id>/', views.unblock_project_step, name='unblock_project_step'),
]
