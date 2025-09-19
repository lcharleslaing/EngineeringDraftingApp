from django.urls import path
from . import views

app_name = "process_creator"

urlpatterns = [
    path("", views.process_list, name="list"),
    path("create/", views.process_create, name="create"),
    path("<int:pk>/", views.process_edit, name="edit"),
    path("<int:pk>/update/", views.process_update, name="update"),
    path("<int:pk>/delete/", views.process_delete, name="delete"),
    path("<int:pk>/pdf/", views.process_pdf, name="pdf"),
    path("<int:pk>/word/", views.process_word, name="word"),
    path("<int:pk>/stats/", views.process_stats, name="stats"),
    # AI endpoints
    path("<int:pk>/ai/summary/", views.process_summary, name="ai_summary"),
    path("<int:pk>/ai/analyze/", views.process_analyze, name="ai_analyze"),
    # AJAX endpoints
    path("<int:pk>/steps/reorder/", views.step_reorder, name="steps_reorder"),
    path("<int:pk>/steps/add/", views.step_add, name="step_add"),
    path("<int:pk>/steps/<int:step_id>/update/", views.step_update, name="step_update"),
    path("<int:pk>/steps/<int:step_id>/delete/", views.step_delete, name="step_delete"),
    path("<int:pk>/steps/<int:step_id>/images/upload/", views.step_image_upload, name="step_image_upload"),
    path("<int:pk>/steps/<int:step_id>/images/<int:image_id>/delete/", views.step_image_delete, name="step_image_delete"),
    # Links & Files (PDF)
    path("<int:pk>/steps/<int:step_id>/links/add/", views.step_link_add, name="step_link_add"),
    path("<int:pk>/steps/<int:step_id>/links/<int:link_id>/delete/", views.step_link_delete, name="step_link_delete"),
    path("<int:pk>/steps/<int:step_id>/files/upload/", views.step_file_upload, name="step_file_upload"),
    path("<int:pk>/steps/<int:step_id>/files/<int:file_id>/delete/", views.step_file_delete, name="step_file_delete"),
    path("<int:pk>/steps/<int:step_id>/images/reorder/", views.step_images_reorder, name="step_images_reorder"),
    # Module management
    path("modules/create/", views.module_create, name="module_create"),
]
