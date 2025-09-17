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
    path("<int:pk>/pdf/", views.process_pdf, name="pdf"),
    path("<int:pk>/word/", views.process_word, name="word"),
    # AJAX endpoints
    path("reorder/", views.processes_reorder, name="reorder"),
    path("<int:pk>/steps/reorder/", views.steps_reorder, name="steps_reorder"),
    path("<int:pk>/steps/add/", views.step_add, name="step_add"),
    path("<int:pk>/steps/<int:step_id>/insert/<str:direction>/", views.step_insert, name="step_insert"),
    path("<int:pk>/steps/<int:step_id>/update/", views.step_update, name="step_update"),
    path("<int:pk>/steps/<int:step_id>/delete/", views.step_delete, name="step_delete"),
    path("<int:pk>/steps/<int:step_id>/images/upload/", views.step_image_upload, name="step_image_upload"),
    path("<int:pk>/steps/<int:step_id>/images/<int:image_id>/delete/", views.step_image_delete, name="step_image_delete"),
    path("print-all/", views.process_print_all, name="print_all"),
]


