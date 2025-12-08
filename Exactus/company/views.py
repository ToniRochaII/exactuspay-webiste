import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse

# Models
from Exactus.company.models import Company
from Exactus.country.models import Country

# Forms & Helpers
from Exactus.company.forms import CompanyForm, CompanyUploadForm
from Exactus.company.registry import get_company_form_class   # ✅ FIXED IMPORT
from Exactus.company.utils.csv_importer import import_from_csv

# Permissions
from Exactus.country.utils.decorators import role_required


# ────────────────────────────────────────────────────────────────
# 🧩 Company Index
# ────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION",
               "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE")
def company(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    companies = Company.objects.filter(country=country).order_by("trade_name")

    return render(request, "company/index.html", {
        "country": country,
        "companies": companies,
        "country_slug": country.slug
    })


# ────────────────────────────────────────────────────────────────
# ➕ Create Company
# ────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION",
               "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE")
def company_create(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)

    # ✅ Correct factory
    FormClass = get_company_form_class(country)

    if request.method == "POST":
        form = FormClass(
            request.POST,
            request.FILES,
            country=country,     # ✅ REQUIRED for country rules!
        )
        if form.is_valid():
            instance = form.save(commit=False)
            instance.country = country
            instance.save()
            return redirect("companies:company", country.slug)
    else:
        form = FormClass(country=country)   # ✅ REQUIRED

    return render(request, "company/form.html", {
        "form": form,
        "country": country,
        "company": None,
    })


# ────────────────────────────────────────────────────────────────
# ✏️ Edit Company
# ────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION",
               "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE")
def company_edit(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)

    # ✅ Correct factory
    FormClass = get_company_form_class(country)

    if request.method == "POST":
        form = FormClass(
            request.POST,
            request.FILES,
            instance=company,
            country=country,    # ✅ REQUIRED
        )
        if form.is_valid():
            instance = form.save(commit=False)
            instance.country = country
            instance.save()
            return redirect("companies:company", country.slug)
    else:
        form = FormClass(
            instance=company,
            country=country,     # ✅ REQUIRED
        )

    return render(request, "company/form.html", {
        "form": form,
        "country": country,
        "company": company,
    })


# ────────────────────────────────────────────────────────────────
# 🗑 Delete Listing (confirmation handled in template)
# ────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION",
               "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE")
def company_delete(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    companies = Company.objects.filter(country=country).order_by("trade_name")

    return render(request, "company/delete.html", {
        "country": country,
        "companies": companies,
        "country_slug": country.slug
    })


# ────────────────────────────────────────────────────────────────
# 📤 Upload Company CSV
# ────────────────────────────────────────────────────────────────

@staff_member_required
def company_upload_view(request, country_slug=None):
    country = None

    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    if request.method == "POST":
        form = CompanyUploadForm(request.POST, request.FILES)

        if form.is_valid():
            dry_run = form.cleaned_data.get("dry_run", False)
            try:
                result = import_from_csv("companies", request.FILES["file"], dry_run=dry_run, country=country)
                request.session["upload_result"] = result

                return redirect(
                    "companies:company_upload_result",
                    country_slug=country_slug
                ) if country_slug else redirect("companies:company_upload_result_global")

            except Exception as e:
                messages.error(request, f"Upload error: {str(e)}")

    else:
        form = CompanyUploadForm()

    return render(request, "company/upload_form.html", {
        "form": form,
        "country": country,
        "country_slug": country_slug
    })


# ────────────────────────────────────────────────────────────────
# 📥 Upload Results
# ────────────────────────────────────────────────────────────────

@staff_member_required
def company_upload_result_view(request, country_slug=None):
    result = request.session.get("upload_result", {})
    country = None

    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    return render(request, "company/upload_result.html", {
        "result": result,
        "country": country,
        "country_slug": country_slug
    })


# ────────────────────────────────────────────────────────────────
# 📄 Download CSV Template
# ────────────────────────────────────────────────────────────────

@staff_member_required
def download_companies_template(request, country_slug=None):
    response = HttpResponse(content_type="text/csv")
    filename = "companies_import_template.csv"

    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
        filename = f"companies_{country.iso2_code}_template.csv"

    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    writer.writerow([
        "country_code", "company_code", "company_number", "trade_name", "legal_name",
        "building_name", "road_name_1", "road_name_2", "town", "post_code",
        "tax_id_1", "tax_id_2", "tax_id_3", "tax_id_4", "tax_id_5",
        "rti_user_id", "rti_password", "account_status"
    ])

    writer.writerow([
        "GB", "COMP001", "12345678", "Example Ltd", "Example Trading Ltd",
        "Tech House", "123 High St", "", "London", "EC1 1AA",
        "PAYE123", "REF456", "", "", "",
        "user_rti", "pass123", "ACTIVE"
    ])

    return response
