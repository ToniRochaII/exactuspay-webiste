from django.db.models.signals import post_save
from django.dispatch import receiver
from Exactus.country.models import Country

@receiver(post_save, sender=Country)
def country_saved(sender, instance, created, **kwargs):
    if created:
        print(f"[SIGNAL] Country Created → {instance.name} ({instance.iso2_code})")
    else:
        print(f"[SIGNAL] Country Updated → {instance.name} ({instance.iso2_code})")
