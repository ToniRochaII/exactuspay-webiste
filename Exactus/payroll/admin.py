from django.contrib import admin
from django.utils.html import format_html
from .models import Payroll, PayrollPeriod, PayrollExecutionLog, PayrollAdjustment

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'fiscal_year', 'country', 'status', 
        'period_count', 'created_at', 'is_editable_display'
    ]
    list_filter = ['status', 'fiscal_year', 'country', 'company']
    search_fields = ['company__name', 'description', 'fiscal_year']
    readonly_fields = ['created_at', 'updated_at', 'locked_at']
    fieldsets = [
        ('Basic Information', {
            'fields': ['company', 'fiscal_year', 'country', 'regulation_version']
        }),
        ('Status', {
            'fields': ['status', 'description']
        }),
        ('Audit Information', {
            'fields': [
                'created_by', 'created_at', 'updated_at',
                'locked_by', 'locked_at'
            ],
            'classes': ['collapse']
        })
    ]
    
    def period_count(self, obj):
        return obj.periods.count()
    period_count.short_description = 'Periods'
    
    def is_editable_display(self, obj):
        return obj.is_editable
    is_editable_display.boolean = True
    is_editable_display.short_description = 'Editable'
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj and not obj.is_editable:
            readonly_fields.extend(['company', 'fiscal_year', 'country'])
        return readonly_fields
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = [
        'payroll', 'period_number', 'name', 'start_date', 'end_date',
        'status', 'employee_count', 'total_amount', 'is_editable_display'
    ]
    list_filter = ['status', 'payroll__company', 'payroll__fiscal_year']
    search_fields = ['name', 'payroll__company__name']
    readonly_fields = [
        'created_at', 'updated_at', 'processed_at', 
        'employee_count', 'total_amount'
    ]
    fieldsets = [
        ('Period Information', {
            'fields': [
                'payroll', 'period_number', 'name',
                'start_date', 'end_date', 'processing_date', 'payment_date'
            ]
        }),
        ('Status & Configuration', {
            'fields': ['status', 'apply_regulations', 'regulation_overrides']
        }),
        ('Results', {
            'fields': [
                'employee_count', 'total_gross', 'total_deductions',
                'total_net', 'total_tax', 'total_amount'
            ],
            'classes': ['collapse']
        }),
        ('Audit Information', {
            'fields': [
                'created_by', 'created_at', 'updated_at',
                'processed_by', 'processed_at'
            ],
            'classes': ['collapse']
        })
    ]
    
    def is_editable_display(self, obj):
        return obj.is_editable
    is_editable_display.boolean = True
    is_editable_display.short_description = 'Editable'
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj and not obj.is_editable:
            readonly_fields.extend([
                'payroll', 'period_number', 'start_date', 'end_date',
                'processing_date', 'payment_date'
            ])
        return readonly_fields
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PayrollExecutionLog)
class PayrollExecutionLogAdmin(admin.ModelAdmin):
    list_display = [
        'period', 'execution_type', 'status', 
        'employee_count', 'started_at', 'processing_time_display'
    ]
    list_filter = ['execution_type', 'status', 'period__payroll__company']
    search_fields = ['period__name', 'error_details']
    readonly_fields = ['started_at', 'completed_at', 'processing_time']
    
    def processing_time_display(self, obj):
        if obj.processing_time:
            total_seconds = obj.processing_time.total_seconds()
            if total_seconds < 60:
                return f"{total_seconds:.1f}s"
            elif total_seconds < 3600:
                return f"{total_seconds/60:.1f}m"
            else:
                return f"{total_seconds/3600:.1f}h"
        return "-"
    processing_time_display.short_description = 'Processing Time'

@admin.register(PayrollAdjustment)
class PayrollAdjustmentAdmin(admin.ModelAdmin):
    list_display = [
        'period', 'adjustment_type', 'description', 
        'amount', 'is_applied', 'created_at'
    ]
    list_filter = ['adjustment_type', 'is_applied', 'period__payroll__company']
    search_fields = ['description', 'regulation_reference']
    readonly_fields = ['created_at', 'updated_at', 'applied_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)