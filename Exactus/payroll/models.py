from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q, UniqueConstraint
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import get_user_model
from Exactus.company.models import Company
from Exactus.country.models import Country
from Exactus.employee.models import Employee
from Exactus.regulations.models import Regulations
import json
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class PeriodStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    PROCESSING = 'PROCESSING', 'Processing'
    COMPLETED = 'COMPLETED', 'Completed'
    LOCKED = 'LOCKED', 'Locked'
    CANCELLED = 'CANCELLED', 'Cancelled'

class Payroll(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payrolls')
    fiscal_year = models.IntegerField()
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='payrolls')
    description = models.TextField(blank=True)
    regulation = models.ForeignKey(Regulations, on_delete=models.PROTECT, related_name='payrolls')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_payrolls')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            UniqueConstraint(fields=['company', 'fiscal_year'], name='unique_payroll_per_company_year')
        ]

    def __str__(self):
        return f'{self.company.trade_name} - FY{self.fiscal_year}'
    
    def get_periods_summary(self):
        periods = self.periods.all()
        return {
            'total_periods': periods.count(),
            'completed': periods.filter(status=PeriodStatus.COMPLETED).count(),
            'locked': periods.filter(status=PeriodStatus.LOCKED).count(),
            'total_amount': sum(p.total_amount or 0 for p in periods)
        }

class PayrollPeriod(models.Model):
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='periods')
    period_number = models.IntegerField()
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    processing_date = models.DateField()
    payment_date = models.DateField()
    status = models.CharField(max_length=20, choices=PeriodStatus.choices, default=PeriodStatus.PENDING)
    
    employee_count = models.IntegerField(default=0)
    total_gross = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_net = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    apply_regulations = models.BooleanField(default=True)
    regulation_overrides = models.JSONField(default=dict, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_periods')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='processed_periods')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['payroll', 'period_number']
        constraints = [
            UniqueConstraint(fields=['payroll', 'period_number'], name='unique_period_number_per_payroll')
        ]

    def __str__(self):
        return f'{self.payroll} - {self.name}'

    @property
    def is_locked(self):
        return self.status in [PeriodStatus.COMPLETED, PeriodStatus.LOCKED]

    @property
    def can_process(self):
        return self.status in [PeriodStatus.PENDING, PeriodStatus.SCHEDULED]

    def mark_as_processing(self, user):
        if self.can_process:
            self.status = PeriodStatus.PROCESSING
            self.processed_by = user
            self.processed_at = timezone.now()
            self.save()
            return True
        return False

    def mark_as_completed(self, results_payload=None):
        """
        Locks the period and Marks Variable components as Processed (Paid).
        """
        # 1. Lock immediately
        self.status = PeriodStatus.LOCKED
        self.processed_at = timezone.now()
        
        if results_payload:
            try:
                self.total_net = Decimal(str(results_payload.get('total_net', 0)))
                self.total_gross = Decimal(str(results_payload.get('total_gross', 0)))
                self.total_tax = Decimal(str(results_payload.get('total_tax', 0)))
                self.total_amount = self.total_net
            except: pass
        
        # 2. MARK COMPONENTS AS PROCESSED
        from Exactus.compensation.models import CompensationComponent
        employees = self.get_eligible_employees()
        
        comps_to_process = CompensationComponent.objects.filter(
            employee__in=employees,
            is_active=True,
            processed=False
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=self.start_date),
            start_date__lte=self.end_date
        )
        
        for comp in comps_to_process:
            # Mark Variable/One-Time items as Paid/Processed
            if comp.category == 'VARIABLE' or comp.frequency == 'one_time':
                comp.mark_processed(period_label=self.name)

        self.save()
        return True

    def get_eligible_employees(self):
        from Exactus.employee.models import Employee
        return Employee.objects.filter(
            company=self.payroll.company,
            employment_start_date__lte=self.end_date
        ).exclude(
            employment_end_date__lt=self.start_date
        )

# ... (PayrollExecutionLog, PayrollAdjustment, PayrollResult remain the same)
class PayrollExecutionLog(models.Model):
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='execution_logs')
    execution_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    input_data = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    output_data = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    error_details = models.TextField(blank=True)
    employee_count = models.IntegerField(default=0)
    processing_time = models.DurationField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

class PayrollAdjustment(models.Model):
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='adjustments')
    adjustment_type = models.CharField(max_length=50)
    description = models.TextField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    affected_employees = models.JSONField(default=list, blank=True)
    regulation_reference = models.CharField(max_length=100, blank=True)
    is_applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, default='pending')

class PayrollResult(models.Model):
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='results')
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='payroll_results')
    gross_pay = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ['period', 'employee']