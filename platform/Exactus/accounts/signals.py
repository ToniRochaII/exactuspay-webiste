from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.db import transaction

from Exactus.accounts.models import PermissionMatrix, User, UserProfile
from Exactus.accounts.utils.access_control import AccessControl


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create UserProfile when a new User is created.
    """
    if created:
        try:
            with transaction.atomic():
                UserProfile.objects.get_or_create(user=instance)
                print(f"✅ Created UserProfile for {instance.username}")  # Debug log
        except Exception as e:
            print(f"❌ Error creating UserProfile for {instance.username}: {e}")


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, **kwargs):
    """
    Ensure UserProfile exists when User is saved (fallback for existing users).
    """
    try:
        # Check if profile exists, create if it doesn't
        if not hasattr(instance, 'userprofile'):
            UserProfile.objects.get_or_create(user=instance)
            print(f"✅ Created missing UserProfile for {instance.username}")  # Debug log
    except Exception as e:
        print(f"❌ Error ensuring UserProfile for {instance.username}: {e}")


@receiver(post_save, sender=PermissionMatrix)
@receiver(post_delete, sender=PermissionMatrix)
def clear_permission_cache(sender, instance, **kwargs):
    """
    Clear permission cache when permissions change.
    """
    if isinstance(instance, PermissionMatrix):
        AccessControl.purge_user_cache()
        print("✅ Cleared permission cache")  # Debug log


@receiver(post_save, sender=User)
def clear_user_permission_cache(sender, instance, **kwargs):
    """
    Clear cache when user role changes.
    """
    # Check if role was actually changed
    if instance.pk and 'role' in getattr(instance, '_changed_fields', []):
        AccessControl.purge_user_cache(instance)
        print(f"✅ Cleared permission cache for {instance.username}")  # Debug log


@receiver(post_save, sender=UserProfile)
def log_profile_save(sender, instance, created, **kwargs):
    """
    Optional: Log when UserProfile is saved (for debugging).
    """
    if created:
        print(f"✅ UserProfile created for {instance.user.username}")
    else:
        print(f"📝 UserProfile updated for {instance.user.username}")