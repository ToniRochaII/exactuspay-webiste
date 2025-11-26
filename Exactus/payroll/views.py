from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from Exactus.payroll.models import Payroll
from Exactus.country.models import Country
from Exactus.company.models import Company
from Exactus.regulations.models import Regulations
from Exactus.payroll.forms import PayrollForm

@login_required
def payroll(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    payrolls = Payroll.objects.filter(company=company)
    return render(request, 'payroll/payroll_list.html', {
        'country': country,
        'company': company,
        'payrolls': payrolls,
        "country_slug": country_slug,
    })

@login_required
def payroll_create(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)  
    if request.method == 'POST':
        form = PayrollForm(request.POST)
        if form.is_valid():
            payroll = form.save(commit=False)
            payroll.country = country
            payroll.company = company
            payroll.save()
            messages.success(request, 'Payroll created successfully.')
            return redirect('payroll:payroll', country_slug=country_slug, company_id=company.company_id)
    else:
        form = PayrollForm()
    return render(request, 'payroll/payroll_form.html', {'form': form, 'country': country, 'company': company, "country_slug": country_slug })

@login_required
def payroll_edit(request, country_slug, pk, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    payroll = get_object_or_404(Payroll, pk=pk)
    if request.method == 'POST':
        form = PayrollForm(request.POST, instance=payroll)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payroll updated successfully.')
            return redirect('payroll:payroll', country_slug=country_slug, company_id=company.company_id)
    else:
        form = PayrollForm(instance=payroll)
    return render(request, 'payroll/payroll_form.html', {'form': form, 'country': country, 'company': company, 'payroll': payroll, "country_slug": country_slug })

@login_required
def payroll_delete(request, country_slug, pk, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    payroll = get_object_or_404(Payroll, pk=pk)
    if request.method == 'POST':
        payroll.delete()
        messages.success(request, 'Payroll deleted successfully.')
        return redirect('payroll:payroll', country_slug=country_slug, company_id=company.company_id)
    return render(request, 'payroll/payroll_confirm_delete.html', {'country': country, 'company': company, 'payroll': payroll, "country_slug": country_slug })


