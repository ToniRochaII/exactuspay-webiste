# regulations/models.py
from django.db import models
from django.utils.text import slugify
import uuid

class Regulations(models.Model):
    country = models.ForeignKey("country.Country", on_delete=models.CASCADE, related_name="regulations")
    fiscal_year = models.IntegerField()
    effective_date = models.DateField()
    slug = models.SlugField(unique=True, blank=True)
    archive = models.CharField(
        "Archive",
        max_length=1,
        choices=[("Y", "YES"), ("N", "NO")],
        default="N",
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.country.name}-{self.fiscal_year}") if self.country and self.fiscal_year else ""
            
            if not base:
                base = uuid.uuid4().hex[:8]

            slug = base
            counter = 1

            while Regulations.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Regulation"
        verbose_name_plural = "Regulations"
        ordering = ["country__name", "-fiscal_year"]
    
    def __str__(self):
        return f"{self.country.name} - {self.fiscal_year}"