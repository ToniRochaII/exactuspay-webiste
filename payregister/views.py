from django.shortcuts import render, get_object_or_404, redirect
from employee.models import Employee
from payregister.models import PayRegister
from payregister.forms import PayRegisterForm
from company.models import  Company
from country.models import Country

def list_entries(request, country_slug, company_id, id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    employee = get_object_or_404(Employee, id=id)
    entries = employee.payregister_entries.all()
    
    return render(request, 'payregister/list.html', {
        'employee': employee,
        'entries': entries,
        'company': company,
        'country': country,
        'country_slug': country_slug,
        
    })

def create_entry(request, country_slug, company_id, id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    employee = get_object_or_404(Employee, id=id)

    if request.method == "POST":
        form = PayRegisterForm(request.POST, company=company)  # ✅ pass company
        if form.is_valid():
            obj = form.save(commit=False)
            obj.employee = employee
            obj.created_by = request.user
            obj.save()
            return redirect(
                "payregister:payregister_list",
                country_slug=country_slug,
                company_id=company.company_id,
                id=id,
            )
    else:
        form = PayRegisterForm(company=company)  # ✅ pass company here too

    return render(
        request,
        "payregister/create.html",
        {
            "employee": employee,
            "form": form,
            "company": company,
            "country": country,
            "country_slug": country_slug,
        },
    )






