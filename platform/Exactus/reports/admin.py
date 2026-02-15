from django.contrib import admin
from .models import ReportCategory, ReportType, ReportLayout, ReportConfiguration

@admin.register(ReportLayout)
class ReportLayoutAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'created_at')
    list_filter = ('report_type',)

@admin.register(ReportConfiguration)
class ReportConfigurationAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'level', 'company', 'country', 'selected_layout')
    list_filter = ('report_type', 'country')
    search_fields = ('company__name', 'country__name')
    
    # Organize the JSON settings field to look cleaner
    fieldsets = (
        ('Scope (Select One)', {
            'fields': ('company', 'country'),
            'description': 'Leave both blank for System Default'
        }),
        ('Configuration', {
            'fields': ('report_type', 'selected_layout', 'data_settings')
        }),
    )

admin.site.register(ReportCategory)
admin.site.register(ReportType)