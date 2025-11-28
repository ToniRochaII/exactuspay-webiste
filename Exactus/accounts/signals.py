from django.db.models.signals import post_save
from django.conf import settings
from django.dispatch import receiver
from Exactus.accounts.models import User, UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Create or update user profile automatically after saving a User.
    Uses get_or_create() to avoid duplicate creation on reloads or multiple signals.
    """
    profile, created_profile = UserProfile.objects.get_or_create(user=instance)
    if not created_profile:
        profile.save()

        
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from Exactus.accounts.models import PermissionMatrix
from Exactus.accounts.utils.access_control import AccessControl


@receiver(post_save, sender=PermissionMatrix)
@receiver(post_delete, sender=PermissionMatrix)
def clear_permission_cache(sender, **kwargs):
    AccessControl.purge_cache()
