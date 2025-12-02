from django.db import models
from Exactus.country.models import Country
from Exactus.company.models import Company
from Exactus.regulations.models import Regulations

class Payroll(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    regulations = models.ForeignKey(Regulations, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    FREQUENCY_CHOICES = [
        ('Annually', 'Annually'),
        ('Monthly', 'Monthly'),
        ('Semi-Monthly', 'Semi-Monthly'),
        ('Fortnightly', 'Fortnightly'),
        ('Weekly', 'Weekly'),
    ]
    payroll_frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)   # NEW
    updated_at = models.DateTimeField(auto_now=True)       # NEW

    def __str__(self):
        return f"{self.regulations} - {self.payroll_frequency}"
