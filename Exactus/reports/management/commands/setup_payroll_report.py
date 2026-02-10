from django.core.management.base import BaseCommand
from Exactus.reports.models import ReportDefinition

class Command(BaseCommand):
    help = 'Creates or updates the Full Payroll Breakdown report definition'

    def handle(self, *args, **kwargs):
        # 1. Define the fields we need to fetch from the database
        # 'details' contains the JSON of all elements and pdcodes
        # 'employee__*' fields are for identification
        fields_to_fetch = [
            'employee__employee_code',
            'employee__employee_name',
            'employee__employee_surname',
            'details',  # <--- This is the key field containing all codes
            'period__payment_date'
        ]

        # 2. Create or Update the Report Definition
        report, created = ReportDefinition.objects.update_or_create(
            name="Full Payroll Breakdown",
            defaults={
                'description': "Complete matrix of all Elements and PD Codes for the selected payroll.",
                'source_model': 'PayrollResult',
                'selected_fields': fields_to_fetch,
                'allow_date_range': True,
                'allow_payroll_selection': True,
                # Set to True if you want to compare two months side-by-side
                'is_comparison': False, 
                # Ensure this is False unless you want YTD totals
                'is_ytd': False 
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Successfully created report: {report.name}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully updated report: {report.name}"))