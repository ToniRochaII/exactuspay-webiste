from decimal import Decimal, InvalidOperation
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q, UniqueConstraint
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import get_user_model
from Exactus.company.models import Company
from Exactus.country.models import Country
from Exactus.employee.models import Employee
from Exactus.regulations.models import Regulations
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class PayrollStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    RUNNING = 'running', 'Running'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    LOCKED = 'locked', 'Locked'

class PeriodStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'              # Stage 1: Open
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    PROCESSING = 'PROCESSING', 'Processing'
    PROCESSED = 'PROCESSED', 'Processed'        # Stage 2: Calculated / Review
    AWAITING_APPROVAL = 'AWAITING_APPROVAL', 'Awaiting Approval' # Stage 3: Locked for Approval
    COMPLETED = 'COMPLETED', 'Completed'        # Stage 4: Finalized
    LOCKED = 'LOCKED', 'Locked'
    CANCELLED = 'CANCELLED', 'Cancelled'

class Payroll(models.Model):
    """
    Payroll master record - One per company per fiscal year
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='payrolls',
        verbose_name='Company'
    )
    fiscal_year = models.IntegerField(
        verbose_name='Fiscal Year',
        help_text='The fiscal year for this payroll'
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name='payrolls',
        verbose_name='Country',
        help_text='Country regulations to apply'
    )
    status = models.CharField(
        max_length=20,
        choices=PayrollStatus.choices,
        default=PayrollStatus.DRAFT,
        verbose_name='Status'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description',
        help_text='Optional description of this payroll'
    )
    regulation = models.ForeignKey(
        Regulations,
        on_delete=models.PROTECT,
        related_name='payrolls',
        verbose_name='Regulation Version',
        help_text='Select the specific regulation version for this fiscal year'
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_payrolls',
        verbose_name='Created By'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    locked_at = models.DateTimeField(null=True, blank=True, verbose_name='Locked At')
    locked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locked_payrolls',
        verbose_name='Locked By'
    )
    
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['company', 'fiscal_year'],
                name='unique_payroll_per_company_year',
                condition=~Q(status=PayrollStatus.CANCELLED)
            )
        ]

        indexes = [
            models.Index(fields=['company', 'fiscal_year']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f'{self.company.trade_name} - FY{self.fiscal_year} - {self.get_status_display()}'
    
    def clean(self):
        super().clean()
        
        # 1. Validate fiscal year
        current_year = timezone.now().year
        if self.fiscal_year < 2000 or self.fiscal_year > current_year + 5:
            raise ValidationError({
                'fiscal_year': f'Fiscal year must be between 2000 and {current_year + 5}'
            })
        
        # 2. Check for duplicate active payroll (excluding cancelled ones)
        if self.pk is None:  # New instance
            duplicate = Payroll.objects.filter(
                company=self.company,
                fiscal_year=self.fiscal_year
            ).exclude(status=PayrollStatus.CANCELLED)
            
            if duplicate.exists():
                raise ValidationError({
                    'fiscal_year': f'A payroll already exists for {self.company.trade_name} '
                                  f'in fiscal year {self.fiscal_year}'
                })

        # 3. Validation: Ensure Regulation Country matches Payroll Country
        if self.regulation and self.country:
            if self.regulation.country != self.country:
                raise ValidationError({
                    'regulation': "The selected regulation does not belong to the payroll's country."
                })

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_editable(self):
        return self.status == PayrollStatus.DRAFT

    @property
    def can_add_periods(self):
        return self.status in [PayrollStatus.DRAFT, PayrollStatus.RUNNING]

    @property
    def is_deletable(self):
        return self.status == PayrollStatus.DRAFT
    
    def lock(self, user):
        """Lock the payroll from further modifications"""
        if self.status not in [PayrollStatus.COMPLETED, PayrollStatus.LOCKED]:
            self.status = PayrollStatus.LOCKED
            self.locked_at = timezone.now()
            self.locked_by = user
            self.save(update_fields=['status', 'locked_at', 'locked_by', 'updated_at'])
    
    def unlock(self):
        """Unlock the payroll for modifications"""
        if self.status == PayrollStatus.LOCKED:
            self.status = PayrollStatus.RUNNING
            self.locked_at = None
            self.locked_by = None
            self.save(update_fields=['status', 'locked_at', 'locked_by', 'updated_at'])
    
    def get_periods_summary(self):
        """Get summary of all periods"""
        periods = self.periods.all()
        return {
            'total_periods': periods.count(),
            'completed': periods.filter(status=PeriodStatus.COMPLETED).count(),
            'pending': periods.filter(status=PeriodStatus.PENDING).count(),
            'locked': periods.filter(status=PeriodStatus.LOCKED).count(),
            'total_amount': sum(p.total_amount or 0 for p in periods),
            'total_employees': sum(p.employee_count or 0 for p in periods)
        }

class PayrollPeriod(models.Model):
    """
    Individual pay period within a payroll
    """
    payroll = models.ForeignKey(
        Payroll,
        on_delete=models.CASCADE,
        related_name='periods',
        verbose_name='Payroll'
    )
    period_number = models.IntegerField(
        verbose_name='Period Number',
        help_text='Sequential period number within the fiscal year'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Period Name',
        help_text='e.g., January 2024, Q1 2024, etc.'
    )
    start_date = models.DateField(verbose_name='Start Date')
    end_date = models.DateField(verbose_name='End Date')
    processing_date = models.DateField(
        verbose_name='Processing Date',
        help_text='Date when payroll should be processed'
    )
    payment_date = models.DateField(
        verbose_name='Payment Date',
        help_text='Date when employees should be paid'
    )
    
    status = models.CharField(
        max_length=20,
        choices=PeriodStatus.choices,
        default=PeriodStatus.PENDING,
        verbose_name='Status'
    )
    
    # Calculation results
    employee_count = models.IntegerField(
        default=0,
        verbose_name='Employee Count'
    )
    total_gross = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Total Gross Amount'
    )
    total_deductions = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Total Deductions'
    )
    total_net = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Total Net Amount'
    )
    total_tax = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Total Tax'
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Total Amount'
    )
    
    # Configuration
    apply_regulations = models.BooleanField(
        default=True,
        verbose_name='Apply Country Regulations'
    )
    regulation_overrides = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Regulation Overrides',
        help_text='JSON overrides for specific regulations'
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_periods',
        verbose_name='Created By'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Processed At')
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_periods',
        verbose_name='Processed By'
    )
    
    class Meta:
        verbose_name = 'Payroll Period'
        verbose_name_plural = 'Payroll Periods'
        ordering = ['payroll', 'period_number']
        constraints = [
            UniqueConstraint(
                fields=['payroll', 'period_number'],
                name='unique_period_number_per_payroll'
            ),
            UniqueConstraint(
                fields=['payroll', 'start_date', 'end_date'],
                name='unique_date_range_per_payroll'
            )
        ]
        indexes = [
            models.Index(fields=['payroll', 'period_number']),
            models.Index(fields=['status']),
            models.Index(fields=['processing_date']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f'{self.payroll} - Period {self.period_number}: {self.name}'
    
    def clean(self):
        super().clean()
        if self.start_date >= self.end_date:
            raise ValidationError("End date must be after start date")

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.name and self.start_date:
            self.name = self.start_date.strftime('%B %Y')
        super().save(*args, **kwargs)
        
    @property
    def is_editable(self):
        return self.status in [PeriodStatus.PENDING, PeriodStatus.SCHEDULED, PeriodStatus.PROCESSED]

    @property
    def is_deletable(self):
        return self.status == PeriodStatus.PENDING

    @property
    def can_process(self):
        return self.status in [PeriodStatus.PENDING, PeriodStatus.SCHEDULED, PeriodStatus.PROCESSED]        

    @property
    def is_locked(self):
        """Check if period is locked"""
        return self.status in [PeriodStatus.AWAITING_APPROVAL, PeriodStatus.COMPLETED, PeriodStatus.LOCKED]

    def lock(self):
        """Lock the period from modifications"""
        if not self.is_locked:
            self.status = PeriodStatus.LOCKED
            self.save(update_fields=['status', 'updated_at'])

    def unlock(self):
        """Unlock the period for modifications"""
        if self.status == PeriodStatus.LOCKED:
            self.status = PeriodStatus.PENDING
            self.save(update_fields=['status', 'updated_at'])

    def mark_as_processing(self, user):
        """Mark period as being processed (Stage 1 -> Engine Running)"""
        if self.can_process:
            self.status = PeriodStatus.PROCESSING
            self.processed_by = user
            self.processed_at = timezone.now()
            self.save(update_fields=[
                'status', 'processed_by', 'processed_at', 'updated_at'
            ])
            return True
        return False

    def mark_as_processed(self, results_payload=None):
        """
        Stage 2: Engine finished. Data is ready for review.
        Status -> PROCESSED.
        """
        self.status = PeriodStatus.PROCESSED
        self.processed_at = timezone.now()
        
        if results_payload:
            # Safely update totals
            try:
                if 'total_net' in results_payload:
                    self.total_net = Decimal(str(results_payload['total_net']))
            except (ValueError, TypeError, InvalidOperation) as e:
                logger.error(f"Error converting total_net: {e}")
                self.total_net = Decimal('0.00')
            
            try:
                if 'total_gross' in results_payload:
                    self.total_gross = Decimal(str(results_payload['total_gross']))
            except (ValueError, TypeError, InvalidOperation) as e:
                logger.error(f"Error converting total_gross: {e}")
                self.total_gross = Decimal('0.00')
            
            # Calculate other totals if provided
            if 'total_tax' in results_payload:
                try:
                    self.total_tax = Decimal(str(results_payload['total_tax']))
                except (ValueError, TypeError, InvalidOperation):
                    self.total_tax = Decimal('0.00')
            
            # Calculate total amount
            self.total_amount = self.total_net
        
        # Update employee count from results
        from .models import PayrollResult
        self.employee_count = PayrollResult.objects.filter(period=self).count()
        
        self.save(update_fields=[
            'status', 'processed_at', 'total_net', 'total_gross',
            'total_tax', 'total_amount', 'employee_count', 'updated_at'
        ])
        
        return True

    def send_for_approval(self):
        """
        Stage 2 -> Stage 3: User sends reviewed payroll for approval.
        Locks the payroll from edits.
        """
        if self.status == PeriodStatus.PROCESSED:
            timestamp = timezone.now()
            PayrollPeriod.objects.filter(pk=self.pk).update(
                status=PeriodStatus.AWAITING_APPROVAL,
                updated_at=timestamp
            )
            self.status = PeriodStatus.AWAITING_APPROVAL
            self.updated_at = timestamp
            return True
        return False

    def authorize(self, user):
        """
        Stage 3 -> Stage 4: Approver authorizes the payroll.
        Finalizes the period AND archives variable AND expired permanent compensations.
        """
        # IMPORT HERE to avoid circular dependency
        from Exactus.compensation.models import CompensationComponent

        if self.status == PeriodStatus.AWAITING_APPROVAL:
            try:
                with transaction.atomic():
                    timestamp = timezone.now()
                    
                    # Get list of employee IDs in this run
                    processed_employee_ids = self.results.values_list('employee_id', flat=True)
                    
                    # -------------------------------------------------------------
                    # 1. Archive Variable/One-time Compensations (Standard Logic)
                    # -------------------------------------------------------------
                    variable_comps_to_archive = CompensationComponent.objects.filter(
                        employee_id__in=processed_employee_ids,
                        processed=False,
                        is_active=True
                    ).filter(
                        # Must be Variable OR One Time
                        Q(category="VARIABLE") | Q(frequency='one_time')
                    ).filter(
                        # Started on or before this period ends
                        start_date__lte=self.end_date
                    )
                    
                    variable_comps_to_archive.update(
                        processed=True,
                        processed_period=self.name,
                        is_active=False, 
                        updated_at=timestamp
                    )

                    # -------------------------------------------------------------
                    # 2. Archive EXPIRED Permanent Compensations (New Logic)
                    # -------------------------------------------------------------
                    # Find Permanent items that are active BUT have an end_date
                    # that is on or before this period's end date.
                    expired_permanent_comps = CompensationComponent.objects.filter(
                        employee_id__in=processed_employee_ids,
                        processed=False,
                        is_active=True,
                        category="PERMANENT",
                        end_date__isnull=False # Must have an end date set
                    ).filter(
                        end_date__lte=self.end_date # The end date has passed
                    )

                    # Mark them as processed/inactive so they move to the Archive list
                    expired_permanent_comps.update(
                        processed=True,
                        processed_period=self.name, # Stamped with the period it expired in
                        is_active=False,
                        updated_at=timestamp
                    )

                    # -------------------------------------------------------------
                    # 3. Update Period Status
                    # -------------------------------------------------------------
                    # We use update() to bypass strict clean() validations if any
                    PayrollPeriod.objects.filter(pk=self.pk).update(
                        status=PeriodStatus.COMPLETED,
                        updated_at=timestamp
                    )
                    
                    self.status = PeriodStatus.COMPLETED
                    self.updated_at = timestamp
                    
                return True
            except Exception as e:
                logger.error(f"Error authorizing payroll period {self.pk}: {e}")
                raise e
        return False

    def reject(self):
        """
        Stage 3 -> Stage 1: Approver rejects the payroll.
        Wipes data and resets to PENDING.
        """
        if self.status == PeriodStatus.AWAITING_APPROVAL:
            timestamp = timezone.now()
            # Use .update() to bypass validation
            PayrollPeriod.objects.filter(pk=self.pk).update(
                status=PeriodStatus.PENDING,
                total_gross=Decimal('0.00'),
                total_net=Decimal('0.00'),
                total_tax=Decimal('0.00'),
                total_amount=Decimal('0.00'),
                employee_count=0,
                updated_at=timestamp
            )
            self.status = PeriodStatus.PENDING
            self.total_gross = Decimal('0.00')
            self.total_net = Decimal('0.00')
            self.total_tax = Decimal('0.00')
            self.total_amount = Decimal('0.00')
            self.employee_count = 0
            self.updated_at = timestamp
            return True
        return False

    # Helper for the dashboard
    def get_eligible_employees(self):
        from Exactus.employee.models import Employee
        return Employee.objects.filter(
            company=self.payroll.company,
            employment_start_date__lte=self.end_date
        ).exclude(
            employment_end_date__lt=self.start_date
        )

    def get_regulation_config(self):
        """Get regulation configuration for this period"""
        config = {
            'country': self.payroll.country.slug,
            'regulation_version': self.payroll.regulation_version,
            'apply_regulations': self.apply_regulations,
            'period_type': 'regular',
            'dates': {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat(),
                'processing': self.processing_date.isoformat() if self.processing_date else None,
                'payment': self.payment_date.isoformat() if self.payment_date else None
            }
        }
        if self.regulation_overrides:
            config.update(self.regulation_overrides)
        return config


class PayrollExecutionLog(models.Model):
    """
    Audit log for payroll period executions
    """
    period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.CASCADE,
        related_name='execution_logs',
        verbose_name='Payroll Period'
    )
    execution_type = models.CharField(
        max_length=50,
        choices=[
            ('calculation', 'Calculation'),
            ('approval', 'Approval'),
            ('payment', 'Payment'),
            ('reporting', 'Reporting'),
            ('adjustment', 'Adjustment')
        ],
        verbose_name='Execution Type'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('started', 'Started'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled')
        ],
        verbose_name='Status'
    )
    
    # Input/Output data
    input_data = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder
    )

    output_data = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder
    )
    error_details = models.TextField(
        blank=True,
        verbose_name='Error Details',
        help_text='Error details if execution failed'
    )
    
    # Statistics
    employee_count = models.IntegerField(default=0, verbose_name='Employee Count')
    processing_time = models.DurationField(null=True, blank=True, verbose_name='Processing Time')
    
    # Audit fields
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Started At')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completed At')
    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payroll_executions',
        verbose_name='Executed By'
    )
    
    class Meta:
        verbose_name = 'Payroll Execution Log'
        verbose_name_plural = 'Payroll Execution Logs'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['period', 'execution_type']),
            models.Index(fields=['status']),
            models.Index(fields=['started_at']),
        ]
    
    def __str__(self):
        return f'{self.period} - {self.execution_type} - {self.status}'
    
    def mark_completed(self, output_data=None):
        """Mark execution as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        
        if output_data:
            self.output_data = output_data
        
        if self.started_at and self.completed_at:
            self.processing_time = self.completed_at - self.started_at
        
        self.save()
    
    def mark_failed(self, error_message):
        """Mark execution as failed"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_details = error_message
        
        if self.started_at and self.completed_at:
            self.processing_time = self.completed_at - self.started_at
        
        self.save()

class PayrollAdjustment(models.Model):
    """
    Adjustments to payroll calculations
    """
    period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.CASCADE,
        related_name='adjustments',
        verbose_name='Payroll Period'
    )
    adjustment_type = models.CharField(
        max_length=50,
        choices=[
            ('bonus', 'Bonus'),
            ('deduction', 'Deduction'),
            ('allowance', 'Allowance'),
            ('correction', 'Correction'),
            ('other', 'Other')
        ],
        verbose_name='Adjustment Type'
    )
    description = models.TextField(verbose_name='Description')
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Amount'
    )
    
    # Affected employees (null means all employees in period)
    affected_employees = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Affected Employees',
        help_text='List of employee IDs affected by this adjustment'
    )
    
    # Regulation reference
    regulation_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Regulation Reference',
        help_text='Reference to specific regulation if applicable'
    )
    
    # Status
    is_applied = models.BooleanField(default=False, verbose_name='Is Applied')
    applied_at = models.DateTimeField(null=True, blank=True, verbose_name='Applied At')
    
    # Audit fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_adjustments',
        verbose_name='Created By'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('applied', 'Applied')
        ],
        default='pending',
        verbose_name='Status'
    )
    
    class Meta:
        verbose_name = 'Payroll Adjustment'
        verbose_name_plural = 'Payroll Adjustments'
        ordering = ['period', '-created_at']
    
    def __str__(self):
        return f'{self.period} - {self.adjustment_type}: {self.description}'
    
    def apply(self):
        """Apply this adjustment to the payroll period"""
        if not self.is_applied:
            self.is_applied = True
            self.applied_at = timezone.now()
            self.save()
            
            # Update period totals
            self.period.total_amount += self.amount
            self.period.save(update_fields=['total_amount', 'updated_at'])

class PayrollResult(models.Model):
    """
    Stores the calculated result (Payslip) for a single employee in a period.
    Required to show individual employee breakdown in dashboard.
    """
    period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.CASCADE,
        related_name='results'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name='payroll_results'
    )
    
    # Financials
    gross_pay = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # JSON breakdown for tax details (INSS, IRRF breakdown)
    details = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Payroll Result'
        verbose_name_plural = 'Payroll Results'
        unique_together = ['period', 'employee']
        ordering = ['employee']