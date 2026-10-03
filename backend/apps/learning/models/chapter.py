import uuid

from django.db import models
from django.db.models.functions import Lower

from apps.learning.validators import normalize_name


class Chapter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(
        "learning.Subject",
        on_delete=models.PROTECT,
        related_name="chapters",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "learning_chapter"
        verbose_name = "chapter"
        verbose_name_plural = "chapters"
        ordering = ["position", "name"]
        constraints = [
            models.UniqueConstraint(
                "subject",
                Lower("name"),
                name="chapter_unique_subject_name_ci",
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.name:
            self.name = normalize_name(self.name)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = normalize_name(self.name)
        super().save(*args, **kwargs)
