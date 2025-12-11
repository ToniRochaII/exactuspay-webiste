"""
Critical fixes for the payroll module
"""

from django.db import models
from django.core.exceptions import ValidationError

# FIX 1: Add missing fields to Payroll model if needed
class PayrollFixed(models.Model):
    """
    Add these fields to your existing Payroll model if you need them
    """
    total_periods = models.IntegerField(default=0, verbose_name='Total Periods')
    completed_periods = models.IntegerField(default=0, verbose_name='Completed Periods')
    total_employees = models.IntegerField(default=0, verbose_name='Total Employees')
    total_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0, 
        verbose_name='Total Amount'
    )
    
    class Meta:
        abstract = True  # This is just for reference

# FIX 2: Update your existing models by adding these fields
# OR remove references to them in signals and templates

# FIX 3: Context processor to ensure variables exist
def payroll_context_processor(request):
    """
    Ensure required context variables exist
    """
    context = {}
    
    # Get company from session or URL
    company_id = request.session.get('company_id')
    country_slug = request.session.get('country_slug')
    
    if company_id:
        from Exactus.company.models import Company
        try:
            context['company'] = Company.objects.get(pk=company_id)
        except Company.DoesNotExist:
            context['company'] = None
    
    if country_slug:
        from Exactus.country.models import Country
        try:
            context['country'] = Country.objects.get(slug=country_slug)
        except Country.DoesNotExist:
            context['country'] = None
    
    return context