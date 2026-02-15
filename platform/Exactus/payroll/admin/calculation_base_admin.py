# Exactus/payroll/admin/calculation_base_admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from Exactus.regulations.models import CalculationBase

@admin.register(CalculationBase)
class CalculationBaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'country', 'element', 'tax_jurisdiction', 'fiscal_year', 'preview_action')
    list_filter = ('country', 'regulations__fiscal_year', 'tax_jurisdiction')
    search_fields = ('element__element_code', 'element__element_name', 'tax_jurisdiction')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('country', 'regulations', 'element', 'element_base')
        }),
        ('Configuration', {
            'fields': ('tax_jurisdiction', 'table_type', 'ss_category', 'base_frequency')
        }),
        ('Allowances', {
            'fields': ('allowance_01', 'allowance_02', 'allowance_03', 'allowance_04', 'allowance_05')
        }),
        ('Brackets', {
            'fields': (
                ('bracket_00', 'rate_00'), ('bracket_01', 'rate_01'),
                ('bracket_02', 'rate_02'), ('bracket_03', 'rate_03'),
                ('bracket_04', 'rate_04'), ('bracket_05', 'rate_05'),
                ('bracket_06', 'rate_06'), ('bracket_07', 'rate_07'),
                ('bracket_08', 'rate_08'), ('bracket_09', 'rate_09'),
                ('bracket_10', 'rate_10'), ('bracket_11', 'rate_11'),
                ('bracket_12', 'rate_12'), ('bracket_13', 'rate_13'),
                ('bracket_14', 'rate_14'), ('bracket_15', 'rate_15'),
            )
        }),
    )
    
    def fiscal_year(self, obj):
        return obj.regulations.fiscal_year
    fiscal_year.short_description = 'Fiscal Year'
    
    def preview_action(self, obj):
        url = reverse('payroll:calculation_preview', kwargs={'base_id': obj.id})
        return format_html('<a class="button" href="{}" target="_blank">Preview</a>', url)
    preview_action.short_description = 'Preview Calculation'