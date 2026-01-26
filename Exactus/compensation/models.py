# Exactus/compensation/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from Exactus.elements.models import Element

User = get_user_model()

class CompensationComponent(models.Model):
    """
    Stores compensation components for employees (salary, bonuses, deductions, etc.)
    """
    employee = models.ForeignKey(
        'employee.Employee',
        on_delete=models.CASCADE,
        related_name='compensation_components'
    )
    
    element = models.ForeignKey(
        Element, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    pd_code = models.ForeignKey(
        'pdcodes.PDCode',
        on_delete=models.CASCADE,
        related_name='components',
        verbose_name='PD Code'
    )
    
    # Amount and frequency
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Amount'
    )
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('weekly', 'Weekly'),
            ('biweekly', 'Bi-weekly'),
            ('annual', 'Annual'),
            ('one_time', 'One Time')
        ],
        default='monthly',
        verbose_name='Frequency'
    )
    
    # Dates
    start_date = models.DateField(verbose_name='Start Date')
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='End Date',
        help_text='Leave blank for ongoing'
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Active')
    processed = models.BooleanField(default=False, verbose_name='Processed')
    processed_period = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Processed Period',
        help_text='Period when this component was processed (e.g., 2024-01)'
    )
    
    # Additional info
    description = models.TextField(blank=True, verbose_name='Description')
    reference = models.CharField(max_length=100, blank=True, verbose_name='Reference')
    
    # Audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_components'
    )

    CATEGORY_PERMANENT = "PERMANENT"
    CATEGORY_VARIABLE = "VARIABLE"

    CATEGORY_CHOICES = [
        (CATEGORY_PERMANENT, "Permanent"),
        # CHANGE 1: Wording update
        (CATEGORY_VARIABLE, "One-Off Payment"),
    ]

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Compensation Component'
        verbose_name_plural = 'Compensation Components'
        ordering = ['employee', '-start_date']
        indexes = [
            models.Index(fields=['employee', 'is_active', 'processed']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        code_str = "Unknown"
        if self.pd_code:
            code_str = str(self.pd_code)
        elif self.element:
            code_str = str(self.element)
        return f"{self.employee} - {code_str}: {self.amount}"
    
    def clean(self):
        super().clean()
        
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError("End date cannot be before start date")
        
        if self.amount <= 0:
            raise ValidationError("Amount must be greater than 0")
    
    def get_period_amount(self, period_start, period_end):
        """
        Calculate the amount for a specific period based on frequency
        """
        from decimal import Decimal
        
        if self.frequency == 'monthly':
            return self.amount
        elif self.frequency == 'weekly':
            # Calculate weeks in period
            days_in_period = (period_end - period_start).days + 1
            weeks = Decimal(days_in_period) / Decimal(7)
            return self.amount * weeks
        elif self.frequency == 'biweekly':
            days_in_period = (period_end - period_start).days + 1
            fortnights = Decimal(days_in_period) / Decimal(14)
            return self.amount * fortnights
        elif self.frequency == 'annual':
            # Prorate annual amount for period
            days_in_period = (period_end - period_start).days + 1
            days_in_year = 365
            return (self.amount / Decimal(days_in_year)) * Decimal(days_in_period)
        elif self.frequency == 'one_time':
            # Check if one-time payment falls within period
            if period_start <= self.start_date <= period_end:
                return self.amount
            return Decimal('0')
        return Decimal('0')
    
    def mark_processed(self, period_label):
        """Mark this component as processed for a period"""
        self.processed = True
        self.processed_period = period_label
        self.save(update_fields=['processed', 'processed_period', 'updated_at'])
    
    def unmark_processed(self):
        """Unmark as processed (for corrections)"""
        self.processed = False
        self.processed_period = ''
        self.save(update_fields=['processed', 'processed_period', 'updated_at'])