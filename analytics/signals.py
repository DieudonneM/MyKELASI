from django.db.models.signals import post_save
from django.dispatch import receiver

from learning.models import LearningEvent

from .models import Event


@receiver(post_save, sender=LearningEvent)
def mirror_learning_event(sender, instance, created, **kwargs):
    if not created:
        return
    Event.objects.create(
        name=instance.name,
        actor_hash=Event.anonymized_actor(instance.actor),
        context=instance.payload or {},
    )
