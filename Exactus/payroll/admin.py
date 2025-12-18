from django.contrib import admin
from .models import Payroll, PayrollPeriod



@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company",
        "fiscal_year",
        "country",
        "status",
        "total_periods",
        "completed_periods",
        "total_employees",
        "total_amount",
        "updated_at",
    )


    def total_periods(self, obj):
        return obj.periods.count()

    def completed_periods(self, obj):
        return obj.periods.filter(status=PeriodStatus.COMPLETED).count()

    def total_employees(self, obj):
        return sum(p.employee_count for p in obj.periods.all())

    def total_amount(self, obj):
        return sum(p.total_amount for p in obj.periods.all())


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = (
        "id", "payroll", "period_number", "name",
        "start_date", "end_date", "processing_date", "payment_date",
        "status", "employee_count",
        "total_gross", "total_tax", "total_net",
        "processed_at",
    )
    list_filter = ("status", "payroll__company", "payroll__country")
    search_fields = ("name", "payroll__company__trade_name", "payroll__company__legal_name")
    ordering = ("payroll", "period_number")
    readonly_fields = ("created_at", "updated_at", "processed_at")




