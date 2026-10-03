import uuid

from django.db import models
from django.db.models.functions import Lower

from apps.learning.validators import normalize_name


class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(
        "learning.Domain",
        on_delete=models.PROTECT,
        related_name="subjects",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "learning_subject"
        verbose_name = "subject"
        verbose_name_plural = "subjects"
        ordering = ["position", "name"]
        constraints = [
            models.UniqueConstraint(
                "domain",
                Lower("name"),
                name="subject_unique_domain_name_ci",
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
