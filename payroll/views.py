from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Payroll
from .models import Country, Company
from regulations.models import Regulations
from .forms import PayrollForm
from django.contrib.auth.decorators import login_required

@login_required
def payroll_list(request, country_id, company_id):
    country = get_object_or_404(Country, id=country_id)
    company = get_object_or_404(Company, company_id=company_id)
    payrolls = Payroll.objects.filter(company=company)
    return render(request, 'payroll/payroll_list.html', {
        'country': country,
        'company': company,
        'payrolls': payrolls
    })

@login_required
def payroll_create(request, country_id, company_id):
    country = get_object_or_404(Country, id=country_id)
    company = get_object_or_404(Company, company_id=company_id)  
    if request.method == 'POST':
        form = PayrollForm(request.POST)
        if form.is_valid():
            payroll = form.save(commit=False)
            payroll.country = country
            payroll.company = company
            payroll.save()
            messages.success(request, 'Payroll created successfully.')
            return redirect('payroll_list', country_id=country.id, company_id=company.company_id)
    else:
        form = PayrollForm()
    return render(request, 'payroll/payroll_form.html', {'form': form, 'country': country, 'company': company})

@login_required
def payroll_edit(request, country_id, company_id, pk):
    country = get_object_or_404(Country, id=country_id)
    company = get_object_or_404(Company, company_id=company_id)
    payroll = get_object_or_404(Payroll, pk=pk)
    if request.method == 'POST':
        form = PayrollForm(request.POST, instance=payroll)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payroll updated successfully.')
            return redirect('payroll_list', country_id=country.id, company_id=company.company_id)
    else:
        form = PayrollForm(instance=payroll)
    return render(request, 'payroll/payroll_form.html', {'form': form, 'country': country, 'company': company, 'payroll': payroll})

@login_required
def payroll_delete(request, country_id, company_id, pk):
    country = get_object_or_404(Country, id=country_id)
    company = get_object_or_404(Company, company_id=company_id)
    payroll = get_object_or_404(Payroll, pk=pk)
    if request.method == 'POST':
        payroll.delete()
        messages.success(request, 'Payroll deleted successfully.')
        return redirect('payroll_list', country_id=country.id, company_id=company.company_id)
    return render(request, 'payroll/payroll_confirm_delete.html', {'country': country, 'company': company, 'payroll': payroll})
