from django.db import models
from django.contrib.auth import get_user_model
from employee.models import Employee
from pdcodes.models import PDcode

User = get_user_model()

class PayRegister(models.Model):

    CATEGORY_CHOICES = [
        ('PERMANENT', 'Permanent'),
        ('TEMPORARY', 'Temporary'),
        ('VARIABLE', 'Variable'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payregister_entries')
    pd_code = models.ForeignKey(PDcode, on_delete=models.PROTECT)

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    amount = models.DecimalField(max_digits=15, decimal_places=2)

    # Permanent and temporary
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Variable requires one date
    entry_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['employee', '-created_at']

    def __str__(self):
        return f"{self.employee} - {self.pd_code.code} ({self.category})"

    @property
    def is_active(self):
        """
        Used by payroll to check if entry applies on a certain date.
        """
        from datetime import date
        today = date.today()

        if self.category == 'PERMANENT':
            if self.end_date and today > self.end_date:
                return False
            if self.start_date and today < self.start_date:
                return False
            return True

        if self.category == 'TEMPORARY':
            return self.start_date <= today <= self.end_date

        if self.category == 'VARIABLE':
            return today == self.entry_date

        return False
