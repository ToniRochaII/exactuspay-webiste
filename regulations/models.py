from django.db import models
from django.utils.text import slugify
import uuid

class Regulations(models.Model):
    country = models.ForeignKey( "country.Country", on_delete=models.CASCADE, related_name="regulations")
    fiscal_year = models.IntegerField()
    effective_date = models.DateField()
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        # Always generate a slug if missing or empty
        if not self.slug:
            base = slugify(self.name) if self.name else ""

            # If name is blank or slugify returns empty, fallback to random id
            if not base:
                base = uuid.uuid4().hex[:8]

            slug = base
            counter = 1

            # Ensure uniqueness
            while Regulations.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)