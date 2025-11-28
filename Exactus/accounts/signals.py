from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

from Exactus.accounts.models import PermissionMatrix, User, UserProfile
from Exactus.accounts.utils.access_control import AccessControl


@receiver(post_save, sender=UserProfile)
@receiver(post_delete, sender=UserProfile)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Ensure every User always has a UserProfile.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=PermissionMatrix)
@receiver(post_delete, sender=PermissionMatrix)
@receiver(m2m_changed, sender=PermissionMatrix)
def clear_permission_cache(sender, instance, **kwargs):
    """
    Clear permission cache when permissions change
    """
    if isinstance(instance, PermissionMatrix):
        # Clear cache for all users with this role
        AccessControl.purge_user_cache()


@receiver(post_save, sender=User)
def clear_user_permission_cache(sender, instance, **kwargs):
    """
    Clear cache when user role changes
    """
    if 'role' in getattr(instance, '_changed_fields', []):
        AccessControl.purge_user_cache(instance)