from django.contrib import admin
from .models import Payroll, PayrollPeriod, PayrollExecutionLog, PayrollResult, PayrollAdjustment

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    # REMOVED 'status' from list_display
    list_display = ('company', 'fiscal_year', 'country', 'regulation', 'created_at')
    # REMOVED 'status' from list_filter
    list_filter = ('company', 'fiscal_year', 'country')
    search_fields = ('company__trade_name', 'description')
    
    # Optional: If you had fieldsets, ensure 'status' is removed there too
    fieldsets = (
        (None, {
            'fields': ('company', 'fiscal_year', 'country', 'regulation', 'description')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'created_by')

@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = (
        'payroll', 'period_number', 'name', 'status', 
        'start_date', 'end_date', 'payment_date'
    )
    list_filter = ('status', 'payroll__company', 'processing_date')
    search_fields = ('name', 'payroll__company__trade_name')
    readonly_fields = (
        'total_gross', 'total_net', 'total_tax', 'total_amount', 
        'employee_count', 'processed_at', 'processed_by'
    )

@admin.register(PayrollExecutionLog)
class PayrollExecutionLogAdmin(admin.ModelAdmin):
    list_display = ('period', 'execution_type', 'status', 'started_at', 'executed_by')
    list_filter = ('status', 'execution_type')
    readonly_fields = ('started_at', 'completed_at', 'input_data', 'output_data', 'error_details')

@admin.register(PayrollResult)
class PayrollResultAdmin(admin.ModelAdmin):
    list_display = ('period', 'employee', 'gross_pay', 'net_pay')
    search_fields = ('employee__employee_name', 'employee__employee_surname')
    list_filter = ('period',)

@admin.register(PayrollAdjustment)
class PayrollAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('period', 'adjustment_type', 'amount', 'status')
    list_filter = ('status', 'adjustment_type')