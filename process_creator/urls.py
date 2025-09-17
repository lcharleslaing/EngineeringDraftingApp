from django.urls import path
from . import views

app_name = "process_creator"

urlpatterns = [
    path("", views.process_list, name="list"),
    path("create/", views.process_create, name="create"),
    path("<int:pk>/", views.process_edit, name="edit"),
    path("<int:pk>/update/", views.process_update, name="update"),
    path("<int:pk>/delete/", views.process_delete, name="delete"),
    path("<int:pk>/print/", views.process_print, name="print"),
    path("<int:pk>/copy/", views.process_copy_prompt, name="copy"),
    # AJAX endpoints
    path("<int:pk>/steps/reorder/", views.steps_reorder, name="steps_reorder"),
    path("<int:pk>/steps/add/", views.step_add, name="step_add"),
    path("<int:pk>/steps/<int:step_id>/update/", views.step_update, name="step_update"),
    path("<int:pk>/steps/<int:step_id>/delete/", views.step_delete, name="step_delete"),
]


