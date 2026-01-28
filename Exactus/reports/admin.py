from django.contrib import admin
from .models import ReportDefinition

@admin.register(ReportDefinition)
class ReportDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'source_model', 'created_at')
    list_filter = ('company', 'source_model')
    search_fields = ('name', 'description')
    
    # This helps visualize the JSON field in the admin panel
    # Depending on your Django version, JSONField has a decent default widget.
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'company', 'created_by')
        }),
        ('Configuration', {
            'fields': ('source_model', 'selected_fields')
        }),
        ('Filters', {
            'fields': ('allow_date_range', 'allow_payroll_selection')
        }),
    )