import uuid

from django.db import models
from django.db.models.functions import Lower

from apps.learning.validators import normalize_name


class Domain(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "learning_domain"
        verbose_name = "domain"
        verbose_name_plural = "domains"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="domain_unique_name_ci",
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
