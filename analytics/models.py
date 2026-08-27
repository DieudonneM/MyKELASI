import hashlib

from django.db import models


class Event(models.Model):
    name = models.CharField(max_length=80)
    actor_hash = models.CharField(max_length=64, blank=True)
    context = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("name", "created_at"))]

    @classmethod
    def anonymized_actor(cls, actor):
        if actor is None:
            return ""
        return hashlib.sha256(str(actor.pk).encode()).hexdigest()

    def __str__(self):
        return self.name
