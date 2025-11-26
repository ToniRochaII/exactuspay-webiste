from django.shortcuts import render, get_object_or_404, redirect
from Exactus.employee.models import Employee
from Exactus.payregister.models import PayRegister
from Exactus.payregister.forms import PayRegisterForm
from Exactus.company.models import  Company
from Exactus.country.models import Country
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from Exactus.payregister.utils.csv_importer import import_payregister_csv
from Exactus.payregister.forms import PayRegisterUploadForm


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






@staff_member_required
def payregister_upload_view(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)

    if request.method == "POST":
        form = PayRegisterUploadForm(request.POST, request.FILES)

        if form.is_valid():
            dry_run = form.cleaned_data.get("dry_run")
            file = request.FILES["file"]

            result = import_payregister_csv(
                file=file,
                company=company,
                created_by=request.user,
                dry_run=dry_run
            )

            request.session["payregister_upload_result"] = result
            messages.success(request, "Upload completed." if not dry_run else "Dry run completed.")
            return redirect("payregister:payregister_upload_result",
                            country_slug=country_slug, company_id=company_id)

    else:
        form = PayRegisterUploadForm()

    return render(request, "payregister/upload_form.html", {
        "form": form,
        "country": country,
        "company": company
    })


@staff_member_required
def payregister_upload_result_view(request, country_slug, company_id):
    result = request.session.get("payregister_upload_result", {})
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)

    return render(request, "payregister/upload_result.html", {
        "result": result,
        "country": country,
        "company": company,
    })


@staff_member_required
def download_payregister_template(request, country_slug, company_id):
    import csv
    from django.http import HttpResponse

    company = get_object_or_404(Company, pk=company_id)

    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = f'attachment; filename="payregister_template_{company.company_code}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "employee_number",
        "pd_code",
        "category",
        "amount",
        "start_date",
        "end_date",
        "entry_date",
    ])

    writer.writerow(["12345", "BASIC", "PERMANENT", "2500.00", "2025-01-01", "", ""])
    writer.writerow(["12345", "OT1", "VARIABLE", "30.00", "", "", "2025-02-05"])

    return response



