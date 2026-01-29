from django.contrib import admin
from .models import ReportDefinition

@admin.register(ReportDefinition)
class ReportDefinitionAdmin(admin.ModelAdmin):
    # Add 'country' to list_display
    list_display = ('name', 'country', 'company', 'source_model', 'created_at')
    
    # Add 'country' to filters
    list_filter = ('country', 'company', 'source_model')
    
    fieldsets = (
        (None, {
            # Add 'country' to the editable fields
            'fields': ('name', 'description', 'country', 'company', 'created_by')
        }),
        ('Configuration', {
            'fields': ('source_model', 'selected_fields')
        }),
        ('Filters', {
            'fields': ('allow_date_range', 'allow_payroll_selection')
        }),
    )