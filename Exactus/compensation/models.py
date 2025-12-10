# Exactus/compensation/models.py
from datetime import timedelta

from django.db import models, transaction


class CompensationComponent(models.Model):
    """
    A recurring or variable payment/deduction component for a single employee.

    - Linked directly to Employee and PD Code.
    - Category = PERMANENT or VARIABLE.
    - PERMANENT: repeats each payroll from start_date until end_date (or forever).
    - VARIABLE: one or multi-period, never prorated (unless PD Code says otherwise).
    """

    CATEGORY_PERMANENT = "PERMANENT"
    CATEGORY_VARIABLE = "VARIABLE"

    CATEGORY_CHOICES = [
        (CATEGORY_PERMANENT, "Permanent"),
        (CATEGORY_VARIABLE, "Variable"),
    ]

    employee = models.ForeignKey(
        "employee.Employee",
        on_delete=models.CASCADE,
        related_name="compensation_components",
    )

    pd_code = models.ForeignKey(
        "pdcodes.PDcode",
        on_delete=models.PROTECT,
        related_name="compensation_components",
    )

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    # Payroll processing flags
    processed = models.BooleanField(
        default=False,
        help_text="True once this component has been processed in payroll.",
    )
    processed_period = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Payroll period identifier, e.g. '2025-03'.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} / {self.pd_code.pdcode_code} / {self.category} / {self.amount}"

    @property
    def is_permanent(self):
        return self.category == self.CATEGORY_PERMANENT

    @property
    def is_variable(self):
        return self.category == self.CATEGORY_VARIABLE

    def is_active_for_period(self, period_start, period_end):
        """
        Business helper: should this component apply to a payroll period?
        Simple date inclusion logic; proration rules will be handled elsewhere.
        """
        if self.processed:
            return False

        if self.is_permanent:
            if self.start_date > period_end:
                return False
            if self.end_date and self.end_date < period_start:
                return False
            return True

        # VARIABLE
        if self.start_date > period_end:
            return False
        if self.end_date and self.end_date < period_start:
            return False
        return True

    def mark_processed(self, period_label: str):
        """
        Mark component as processed for a given payroll period.
        """
        self.processed = True
        self.processed_period = period_label
        self.save(update_fields=["processed", "processed_period", "updated_at"])

    def save(self, *args, **kwargs):
        """
        Custom save to implement: 
        - Auto-closing previous PERMANENT component with same PD code for the same employee.

        Rule:
        If this is a NEW PERMANENT component with a start_date S,
        and there is an older PERMANENT component with same employee+pd_code
        whose end_date is NULL, set that older component's end_date to S - 1 day.
        """
        is_new = self.pk is None

        with transaction.atomic():
            if (
                is_new
                and self.category == self.CATEGORY_PERMANENT
                and self.start_date is not None
            ):
                # Close any open-ended previous permanent component for this PD code
                previous_qs = CompensationComponent.objects.filter(
                    employee=self.employee,
                    pd_code=self.pd_code,
                    category=self.CATEGORY_PERMANENT,
                    end_date__isnull=True,
                ).exclude(pk=self.pk)

                if previous_qs.exists():
                    new_end = self.start_date - timedelta(days=1)
                    previous_qs.update(end_date=new_end)

            super().save(*args, **kwargs)
