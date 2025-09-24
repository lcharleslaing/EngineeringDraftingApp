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
    path("<int:pk>/stats/", views.process_stats, name="stats"),
    # AI endpoints
    path("<int:pk>/ai/summary/", views.ai_generate_summary, name="ai_summary"),
    path("<int:pk>/ai/analyze/", views.ai_analyze_process, name="ai_analyze"),
    # AJAX endpoints
    path("reorder/", views.processes_reorder, name="reorder"),
    path("<int:pk>/steps/reorder/", views.steps_reorder, name="steps_reorder"),
    path("<int:pk>/steps/add/", views.step_add, name="step_add"),
    path("<int:pk>/steps/<int:step_id>/insert/<str:direction>/", views.step_insert, name="step_insert"),
    path("<int:pk>/steps/<int:step_id>/update/", views.step_update, name="step_update"),
    path("<int:pk>/steps/<int:step_id>/delete/", views.step_delete, name="step_delete"),
    path("<int:pk>/steps/<int:step_id>/images/upload/", views.step_image_upload, name="step_image_upload"),
    path("<int:pk>/steps/<int:step_id>/images/<int:image_id>/delete/", views.step_image_delete, name="step_image_delete"),
    path("<int:pk>/steps/<int:step_id>/images/<int:image_id>/update-substep/", views.step_image_update_substep, name="step_image_update_substep"),
    path("<int:pk>/steps/<int:step_id>/images/clear-substeps/", views.step_images_clear_substeps, name="step_images_clear_substeps"),
    # Links & Files (PDF)
    path("<int:pk>/steps/<int:step_id>/links/add/", views.step_link_add, name="step_link_add"),
    path("<int:pk>/steps/<int:step_id>/links/<int:link_id>/delete/", views.step_link_delete, name="step_link_delete"),
    path("<int:pk>/steps/<int:step_id>/files/upload/", views.step_file_upload, name="step_file_upload"),
    path("<int:pk>/steps/<int:step_id>/files/<int:file_id>/delete/", views.step_file_delete, name="step_file_delete"),
    path("<int:pk>/steps/<int:step_id>/images/reorder/", views.step_images_reorder, name="step_images_reorder"),
    path("print-all/", views.process_print_all, name="print_all"),
    # Module management
    path("modules/", views.module_manage, name="module_manage"),
    path("modules/create/", views.module_create, name="module_create"),
    path("modules/<int:module_id>/update/", views.module_update, name="module_update"),
    path("modules/<int:module_id>/delete/", views.module_delete, name="module_delete"),
    # Bulk operations
    path("bulk/summary/", views.bulk_summary, name="bulk_summary"),
    path("bulk/analyze/", views.bulk_analyze, name="bulk_analyze"),
    path("bulk/pdf/", views.bulk_pdf, name="bulk_pdf"),
    path("bulk/word/", views.bulk_word, name="bulk_word"),
    # Templates
    path("templates/", views.template_list, name="template_list"),
    path("templates/<int:tpl_id>/", views.template_detail, name="template_detail"),
    # Jobs
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/create/<int:tpl_id>/", views.job_create, name="job_create"),
    path("jobs/<int:job_id>/", views.job_detail, name="job_detail"),
    path("jobs/<int:job_id>/start/", views.job_start, name="job_start"),
    path("jobs/<int:job_id>/steps/<int:job_step_id>/start/", views.job_step_start, name="job_step_start"),
    path("jobs/<int:job_id>/steps/<int:job_step_id>/complete/", views.job_step_complete, name="job_step_complete"),
    path("jobs/<int:job_id>/steps/<int:job_step_id>/block/", views.job_step_block, name="job_step_block"),
    path("jobs/<int:job_id>/steps/<int:job_step_id>/unblock/", views.job_step_unblock, name="job_step_unblock"),
    # Job Exports
    path("jobs/<int:job_id>/print/", views.job_print, name="job_print"),
    path("jobs/<int:job_id>/pdf/", views.job_pdf, name="job_pdf"),
    path("jobs/<int:job_id>/word/", views.job_word, name="job_word"),
    # Publish template
    path("templates/<int:tpl_id>/publish/", views.template_publish, name="template_publish"),
    path("templates/create-from-selected/", views.template_create_from_selected, name="template_create_from_selected"),
    # Subtasks and update-from-template
    path("subtasks/<int:subtask_id>/toggle/", views.job_subtask_toggle, name="job_subtask_toggle"),
    path("jobs/<int:job_id>/update-from-template/", views.job_update_from_template, name="job_update_from_template"),
    path("steps/<int:job_step_id>/notes/", views.job_step_notes_update, name="job_step_notes_update"),
    path("steps/<int:job_step_id>/images/upload/", views.job_step_image_upload, name="job_step_image_upload"),
    path("steps/<int:job_step_id>/images/<int:image_id>/delete/", views.job_step_image_delete, name="job_step_image_delete"),
]


