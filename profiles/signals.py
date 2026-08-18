from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User

from .models import LearnerProfile, TeacherProfile


@receiver(post_save, sender=User)
def create_public_profile(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.account_type == User.AccountType.LEARNER:
        LearnerProfile.objects.get_or_create(user=instance)
    elif instance.account_type == User.AccountType.TEACHER:
        TeacherProfile.objects.get_or_create(user=instance)
