# Exactus/payroll/signals.py
"""
Signals for the Payroll module to handle business logic automatically.

Key signals:
1. Prevent deletion of processed periods
2. Update payroll status based on periods
3. Validate date overlaps
4. Handle status transitions
5. Log important changes
"""

from django.db.models.signals import pre_save, post_save, pre_delete, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
import logging

from .models import Payroll, PayrollPeriod, PayrollStatus, PeriodStatus, PayrollExecutionLog

logger = logging.getLogger(__name__)

# ============================================================================
# PAYROLL SIGNALS
# ============================================================================

@receiver(pre_save, sender=Payroll)
def validate_payroll_unique_constraint(sender, instance, **kwargs):
    """
    Validate unique payroll per company per fiscal year before saving.
    This provides a better error message than the database constraint.
    """
    if instance.pk is None:  # New instance
        # Check for existing payroll for same company and year (excluding cancelled)
        existing = Payroll.objects.filter(
            company=instance.company,
            fiscal_year=instance.fiscal_year
        ).exclude(status=PayrollStatus.CANCELLED)
        
        if existing.exists():
            raise ValidationError(
                f"A payroll already exists for {instance.company.trade_name} "
                f"in fiscal year {instance.fiscal_year}"
            )
    
    # Validate fiscal year range
    current_year = timezone.now().year
    if instance.fiscal_year < 2000 or instance.fiscal_year > current_year + 5:
        raise ValidationError(
            f"Fiscal year must be between 2000 and {current_year + 5}"
        )


@receiver(pre_save, sender=Payroll)
def handle_payroll_status_transitions(sender, instance, **kwargs):
    """
    Handle payroll status transitions with business rules.
    """
    if instance.pk:  # Only for existing instances
        try:
            old_instance = Payroll.objects.get(pk=instance.pk)
            
            # Rule 1: Once COMPLETED or LOCKED, cannot go back to DRAFT/RUNNING
            if old_instance.status in [PayrollStatus.COMPLETED, PayrollStatus.LOCKED]:
                if instance.status in [PayrollStatus.DRAFT, PayrollStatus.RUNNING]:
                    raise ValidationError(
                        f"Cannot change status from {old_instance.status} to {instance.status}"
                    )
            
            # Rule 2: Set locked_at timestamp when locking
            if instance.status == PayrollStatus.LOCKED and old_instance.status != PayrollStatus.LOCKED:
                instance.locked_at = timezone.now()
            
            # Rule 3: Clear locked_at when unlocking
            if old_instance.status == PayrollStatus.LOCKED and instance.status != PayrollStatus.LOCKED:
                instance.locked_at = None
                instance.locked_by = None
            
        except Payroll.DoesNotExist:
            pass  # New instance


@receiver(post_save, sender=Payroll)
def create_initial_periods_for_payroll(sender, instance, created, **kwargs):
    """
    Automatically create initial periods when a new payroll is created.
    This is optional and can be configured via settings.
    """
    if created:
        # Check if we should create default periods
        # You could make this configurable via settings or payroll type
        from django.conf import settings
        
        auto_create_periods = getattr(settings, 'PAYROLL_AUTO_CREATE_PERIODS', False)
        
        if auto_create_periods:
            try:
                from datetime import date
                
                # Create 12 monthly periods for the fiscal year
                for month in range(1, 13):
                    # Calculate dates (simplified - adjust based on your fiscal calendar)
                    start_date = date(instance.fiscal_year, month, 1)
                    
                    # Calculate end date (last day of month)
                    if month == 12:
                        end_date = date(instance.fiscal_year, 12, 31)
                    else:
                        end_date = date(instance.fiscal_year, month + 1, 1)
                        end_date = end_date.replace(day=end_date.day - 1)
                    
                    # Processing date: 5th of next month
                    processing_month = month + 1 if month < 12 else 1
                    processing_year = instance.fiscal_year if month < 12 else instance.fiscal_year + 1
                    processing_date = date(processing_year, processing_month, 5)
                    
                    PayrollPeriod.objects.create(
                        payroll=instance,
                        period_number=month,
                        name=f"{start_date.strftime('%B %Y')}",
                        start_date=start_date,
                        end_date=end_date,
                        processing_date=processing_date,
                        created_by=instance.created_by
                    )
                
                logger.info(f"Created 12 monthly periods for payroll {instance}")
                
            except Exception as e:
                logger.error(f"Failed to create initial periods for payroll {instance}: {e}")


@receiver(post_save, sender=Payroll)
def log_payroll_status_change(sender, instance, created, **kwargs):
    """
    Log payroll status changes for audit trail.
    """
    if not created and instance.pk:
        try:
            old_instance = Payroll.objects.get(pk=instance.pk)
            
            if old_instance.status != instance.status:
                logger.info(
                    f"Payroll {instance} status changed from "
                    f"{old_instance.status} to {instance.status}"
                )
                
                # You could create an audit log entry here
                # AuditLog.objects.create(
                #     payroll=instance,
                #     action='status_change',
                #     old_value=old_instance.status,
                #     new_value=instance.status,
                #     user=get_current_user()  # You'd need to implement this
                # )
                
        except Payroll.DoesNotExist:
            pass


# ============================================================================
# PAYROLL PERIOD SIGNALS
# ============================================================================

@receiver(pre_save, sender=PayrollPeriod)
def validate_period_dates(sender, instance, **kwargs):
    """
    Validate period dates before saving.
    """
    # Basic date validation
    if instance.start_date >= instance.end_date:
        raise ValidationError("End date must be after start date")
    
    if instance.processing_date and instance.processing_date > instance.end_date:
        raise ValidationError("Processing date must be on or after end date")
    
    # Check for overlapping periods (excluding self)
    if instance.pk:  # For updates
        overlapping = PayrollPeriod.objects.filter(
            payroll=instance.payroll,
            start_date__lt=instance.end_date,
            end_date__gt=instance.start_date
        ).exclude(pk=instance.pk)
    else:  # For new periods
        overlapping = PayrollPeriod.objects.filter(
            payroll=instance.payroll,
            start_date__lt=instance.end_date,
            end_date__gt=instance.start_date
        )
    
    if overlapping.exists():
        raise ValidationError(
            f"Period overlaps with existing period(s): "
            f"{', '.join(str(p) for p in overlapping)}"
        )


@receiver(pre_save, sender=PayrollPeriod)
def validate_period_editable(sender, instance, **kwargs):
    """
    Prevent editing of non-editable periods.
    """
    if instance.pk:  # Only for existing instances
        try:
            old_instance = PayrollPeriod.objects.get(pk=instance.pk)
            
            # If period is not editable and certain fields are changed
            if not old_instance.is_editable:
                # Check which fields are being changed
                changed_fields = []
                for field in ['start_date', 'end_date', 'processing_date', 'period_number', 'name']:
                    if getattr(old_instance, field) != getattr(instance, field):
                        changed_fields.append(field)
                
                if changed_fields:
                    raise ValidationError(
                        f"Cannot edit period {instance}: it is not editable. "
                        f"Attempted to change: {', '.join(changed_fields)}"
                    )
        
        except PayrollPeriod.DoesNotExist:
            pass  # New instance


@receiver(pre_delete, sender=PayrollPeriod)
def prevent_delete_processed_period(sender, instance, **kwargs):
    """
    Prevent deletion of periods that are not deletable.
    """
    if not instance.is_deletable:
        raise ValidationError(
            f"Cannot delete period {instance}: it is not deletable "
            f"(current status: {instance.get_status_display()})"
        )


@receiver(pre_save, sender=PayrollPeriod)
def handle_period_status_transitions(sender, instance, **kwargs):
    """
    Handle period status transitions with business rules.
    """
    if instance.pk:  # Only for existing instances
        try:
            old_instance = PayrollPeriod.objects.get(pk=instance.pk)
            
            # Rule 1: Once COMPLETED or LOCKED, cannot go back
            if old_instance.status in [PeriodStatus.COMPLETED, PeriodStatus.LOCKED]:
                if instance.status in [PeriodStatus.PENDING, PeriodStatus.SCHEDULED, PeriodStatus.PROCESSING]:
                    raise ValidationError(
                        f"Cannot change status from {old_instance.status} to {instance.status}"
                    )
            
            # Rule 2: When marking as PROCESSING, set processed_by and processed_at
            if (instance.status == PeriodStatus.PROCESSING and 
                old_instance.status != PeriodStatus.PROCESSING):
                # This should be set by the view/process that initiates processing
                # The signal ensures it's set if not already
                if not instance.processed_at:
                    instance.processed_at = timezone.now()
            
            # Rule 3: When marking as COMPLETED, ensure it was PROCESSING
            if (instance.status == PeriodStatus.COMPLETED and 
                old_instance.status != PeriodStatus.COMPLETED):
                if old_instance.status != PeriodStatus.PROCESSING:
                    raise ValidationError(
                        "Can only complete a period that is currently processing"
                    )
            
            # Rule 4: Auto-lock payroll when all periods are completed
            if instance.status == PeriodStatus.COMPLETED:
                # Check if all periods in this payroll are now completed
                all_periods_completed = not instance.payroll.periods.exclude(
                    status=PeriodStatus.COMPLETED
                ).exists()
                
                if all_periods_completed:
                    instance.payroll.status = PayrollStatus.COMPLETED
                    instance.payroll.save()
        
        except PayrollPeriod.DoesNotExist:
            pass  # New instance


@receiver(post_save, sender=PayrollPeriod)
def update_payroll_totals(sender, instance, **kwargs):
    """
    Update payroll totals when periods are saved.
    This is done asynchronously to avoid blocking.
    """
    # Use transaction.on_commit to ensure we're outside the current transaction
    transaction.on_commit(lambda: _update_payroll_totals_async(instance.payroll_id))


def _update_payroll_totals_async(payroll_id):
    """
    Async function to update payroll totals.
    """
    try:
        payroll = Payroll.objects.get(pk=payroll_id)
        
        # Calculate totals from all periods
        periods = payroll.periods.all()
        
        payroll.total_periods = periods.count()
        payroll.completed_periods = periods.filter(status=PeriodStatus.COMPLETED).count()
        payroll.total_employees = sum(p.employee_count for p in periods)
        payroll.total_amount = sum(p.total_amount for p in periods)
        
        # Update status based on periods
        if payroll.completed_periods == payroll.total_periods > 0:
            payroll.status = PayrollStatus.COMPLETED
        elif payroll.completed_periods > 0:
            payroll.status = PayrollStatus.RUNNING
        
        payroll.save(update_fields=['updated_at'])
        
    except Payroll.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Error updating payroll totals for payroll_id={payroll_id}: {e}")


@receiver(post_save, sender=PayrollPeriod)
def log_period_creation(sender, instance, created, **kwargs):
    """
    Log period creation for audit trail.
    """
    if created:
        logger.info(f"Created period {instance} for payroll {instance.payroll}")


# ============================================================================
# PAYROLL EXECUTION LOG SIGNALS
# ============================================================================

@receiver(pre_save, sender=PayrollExecutionLog)
def validate_execution_log(sender, instance, **kwargs):
    """
    Validate execution log before saving.
    """
    # Ensure period belongs to the same company as the user's permissions allow
    # (Add your permission logic here)
    pass


@receiver(post_save, sender=PayrollExecutionLog)
def update_period_from_execution(sender, instance, created, **kwargs):
    """
    Update period status based on execution log results.
    """
    if created and instance.status == 'completed':
        try:
            period = instance.period
            
            # Extract results from output_data
            results = instance.output_data.get('results', {})
            
            if results.get('success', False):
                # Update period with results
                period.employee_count = results.get('employee_count', 0)
                period.total_amount = results.get('total_amount', 0)
                period.total_gross = results.get('total_gross', 0)
                period.total_deductions = results.get('total_deductions', 0)
                period.total_net = results.get('total_net', 0)
                period.total_tax = results.get('total_tax', 0)
                
                # Mark as completed
                if period.status == PeriodStatus.PROCESSING:
                    period.status = PeriodStatus.COMPLETED
                
                period.save()
                logger.info(f"Updated period {period} from execution log {instance}")
            
        except Exception as e:
            logger.error(f"Error updating period from execution log {instance}: {e}")


@receiver(post_save, sender=PayrollExecutionLog)
def handle_failed_execution(sender, instance, created, **kwargs):
    """
    Handle failed executions by resetting period status.
    """
    if created and instance.status == 'failed':
        try:
            period = instance.period
            
            # Reset period status if it was processing
            if period.status == PeriodStatus.PROCESSING:
                period.status = PeriodStatus.PENDING
                period.save()
                logger.warning(f"Reset period {period} to PENDING due to failed execution")
            
        except Exception as e:
            logger.error(f"Error handling failed execution for log {instance}: {e}")


# ============================================================================
# BULK OPERATION SIGNALS
# ============================================================================

@receiver(m2m_changed)
def handle_bulk_period_operations(sender, instance, action, **kwargs):
    """
    Handle bulk operations on periods (if using ManyToMany for something).
    This is a template for future expansion.
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        # Handle bulk updates here
        pass


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def connect_all_signals():
    """
    Connect all signals. Call this in apps.py ready() method.
    """
    # Signals are automatically connected via @receiver decorators
    # This function is for explicit control if needed
    pass


def disconnect_all_signals():
    """
    Disconnect all signals (useful for testing).
    """
    from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
    
    # Disconnect payroll signals
    pre_save.disconnect(validate_payroll_unique_constraint, sender=Payroll)
    pre_save.disconnect(handle_payroll_status_transitions, sender=Payroll)
    post_save.disconnect(create_initial_periods_for_payroll, sender=Payroll)
    post_save.disconnect(log_payroll_status_change, sender=Payroll)
    
    # Disconnect period signals
    pre_save.disconnect(validate_period_dates, sender=PayrollPeriod)
    pre_save.disconnect(validate_period_editable, sender=PayrollPeriod)
    pre_delete.disconnect(prevent_delete_processed_period, sender=PayrollPeriod)
    pre_save.disconnect(handle_period_status_transitions, sender=PayrollPeriod)
    post_save.disconnect(update_payroll_totals, sender=PayrollPeriod)
    post_save.disconnect(log_period_creation, sender=PayrollPeriod)
    
    # Disconnect execution log signals
    pre_save.disconnect(validate_execution_log, sender=PayrollExecutionLog)
    post_save.disconnect(update_period_from_execution, sender=PayrollExecutionLog)
    post_save.disconnect(handle_failed_execution, sender=PayrollExecutionLog)


# ============================================================================
# TEST SIGNALS (Development only)
# ============================================================================

@receiver(post_save, sender=Payroll)
def development_test_signal(sender, instance, created, **kwargs):
    """
    Development-only signal for testing.
    Remove in production.
    """
    import os
    if os.environ.get('DJANGO_DEVELOPMENT', False):
        logger.debug(f"Payroll signal fired: {instance} created={created}")