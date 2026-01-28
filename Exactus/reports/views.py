import csv
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import ReportDefinition
from .forms import RunReportForm
from .engine import ReportEngine
from Exactus.company.models import Company
from Exactus.country.models import Country

@login_required
def report_list(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    reports = ReportDefinition.objects.filter(company=company)
    return render(request, 'reports/list.html', {'company': company, 'reports': reports, 'country': country})

@login_required
def report_run(request, country_slug, company_id, report_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    report_def = get_object_or_404(ReportDefinition, pk=report_id, company=company)
    
    results = None
    columns = []

    if request.method == 'POST':
        form = RunReportForm(request.POST, company_id=company_id, report_def=report_def)
        if form.is_valid():
            # Extract data
            s_date = form.cleaned_data.get('start_date')
            e_date = form.cleaned_data.get('end_date')
            payroll_obj = form.cleaned_data.get('payroll')
            p_id = payroll_obj.id if payroll_obj else None

            # RUN ENGINE
            engine = ReportEngine(report_def, company_id)
            results = engine.generate(start_date=s_date, end_date=e_date, payroll_id=p_id)
            
            if results:
                columns = list(results[0].keys())
                
            # Handle Export to CSV Action
            if 'export_csv' in request.POST:
                return export_to_csv(report_def.name, columns, results)

    else:
        form = RunReportForm(company_id=company_id, report_def=report_def)

    return render(request, 'reports/run.html', {
        'country': country,
        'company': company, 
        'report_def': report_def, 
        'form': form,
        'results': results,
        'columns': columns
    })

def export_to_csv(filename, columns, data):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    writer = csv.DictWriter(response, fieldnames=columns)
    writer.writeheader()
    for row in data:
        writer.writerow(row)
        
    return response