from django.db import models
from django.utils.text import slugify

class Regulations(models.Model):
    country = models.ForeignKey( "country.Country", on_delete=models.CASCADE, related_name="regulations")
    fiscal_year = models.IntegerField()
    effective_date = models.DateField()
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def __str__(self):
        return f" {str(self.fiscal_year)} {self.country}"