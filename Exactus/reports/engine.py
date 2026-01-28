from django.apps import apps
from django.db.models import F

class ReportEngine:
    def __init__(self, report_definition, company_id):
        self.report_def = report_definition
        self.company_id = company_id

    def generate(self, start_date=None, end_date=None, payroll_id=None):
        """
        Executes the report and returns a Pandas DataFrame or list of dicts.
        """
        # 1. Resolve the Model
        # We assume the models are in specific apps. Adjust 'app_label' as needed.
        if self.report_def.source_model == 'PayrollResult':
            Model = apps.get_model('payroll', 'PayrollResult')
        elif self.report_def.source_model == 'Employee':
            Model = apps.get_model('employee', 'Employee')
        elif self.report_def.source_model == 'PayrollPeriod':
            Model = apps.get_model('payroll', 'PayrollPeriod')
        else:
            raise ValueError(f"Unknown source model: {self.report_def.source_model}")

        # 2. Start Query
        # Filter by company generally (assuming the model has a company link)
        # Note: PayrollResult links to Employee which links to Company
        if self.report_def.source_model == 'PayrollResult':
            qs = Model.objects.filter(employee__company_id=self.company_id)
        elif self.report_def.source_model == 'Employee':
            qs = Model.objects.filter(company_id=self.company_id)
        elif self.report_def.source_model == 'PayrollPeriod':
            qs = Model.objects.filter(payroll__company_id=self.company_id)

        # 3. Apply Runtime Parameters
        if self.report_def.allow_date_range and start_date and end_date:
            if self.report_def.source_model == 'PayrollResult':
                qs = qs.filter(period__payment_date__range=[start_date, end_date])
            elif self.report_def.source_model == 'PayrollPeriod':
                qs = qs.filter(payment_date__range=[start_date, end_date])
            # Employees usually don't filter by payment date range unless using joined data

        if self.report_def.allow_payroll_selection and payroll_id:
            if self.report_def.source_model == 'PayrollResult':
                qs = qs.filter(period__payroll_id=payroll_id)
            elif self.report_def.source_model == 'PayrollPeriod':
                qs = qs.filter(payroll_id=payroll_id)

        # 4. Select Dynamic Fields
        # We map the JSON list to Django's values() call
        fields_to_fetch = self.report_def.selected_fields
        
        # Safe extraction
        data = list(qs.values(*fields_to_fetch))

        return data