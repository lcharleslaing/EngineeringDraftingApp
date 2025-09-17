from django.db import models


class Process(models.Model):
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name


class Step(models.Model):
    process = models.ForeignKey(Process, related_name="steps", on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("process", "order")

    def __str__(self) -> str:
        return f"{self.order}. {self.title}"


class StepImage(models.Model):
    step = models.ForeignKey(Step, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="process_screenshots/")
    order = models.PositiveIntegerField(default=1)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]

# Create your models here.
