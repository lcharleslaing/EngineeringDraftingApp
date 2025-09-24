from django.conf import settings

# Configurable label for "Job" entities used in UI
JOB_LABEL = getattr(settings, "PROCESS_CREATOR_JOB_LABEL", "Job")


