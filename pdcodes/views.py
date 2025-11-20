from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from utils.decorators import role_required
from .models import Company, PDcode
from country.models import Country
from forms import PDcodeForm


# ────────────────────────────────────────────────────────────────
# LIST ELEMENTS
# ────────────────────────────────────────────────────────────────
@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def pdcode(request, country_slug,company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    pdcodes = PDcode.objects.filter(company=company).order_by("pdcode_code")
    return render(
        request,
        "pdcodes/index.html",
        {"company": company, "pdcodes": pdcodes, "country":country, "country_slug":country_slug},
    )

# ────────────────────────────────────────────────────────────────
# CREATE ELEMENT
# ────────────────────────────────────────────────────────────────
@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def pdcode_create(request, country_slug,company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)

    form = PDcodeForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        pdcode = form.save(commit=False)
        pdcode.company = company
        pdcode.save()

        messages.success(
            request,
            f"PDcode '{pdcode.pdcode_code} – {pdcode.pdcode_name}' created successfully."
        )
        return redirect("pdcodes:pdcodes", company_id=company.company_id)

    return render(
        request,
        "pdcodes/create.html",
        {
            "form": form,
            "company": company,
            "company_id": company_id,
            "country": country,
            "country_slug": country_slug,
        },
    )



# ────────────────────────────────────────────────────────────────
# EDIT ELEMENT

@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def pdcode_edit(request, country_slug, company_id, pdcode_code):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    pdcode = get_object_or_404(PDcode, pdcode_code=pdcode_code, company=company)

    if request.method == "POST":
        form = PDcodeForm(request.POST, instance=pdcode)
        if form.is_valid():
            form.save()
            messages.success(request, f"PDcode '{pdcode.pdcode_code} | {pdcode.pdcode_name}' updated successfully.")
            return redirect("pdcodes:pdcodes", company_id=company.company_id)
    else:
        form = PDcodeForm(instance=pdcode)

    return render(
        request,
        "pdcodes/edit.html",
        {"form": form, "company": company, "pdcode": pdcode, "company_id":company_id, "country": country, "country_slug":country_slug},
    )


# ────────────────────────────────────────────────────────────────
# DELETE ELEMENT
# ────────────────────────────────────────────────────────────────
@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def pdcode_delete(request, country_slug, company_id, pdcode_code):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    pdcode = get_object_or_404(PDcode, pdcode_code=pdcode_code, company=company)

    if request.method == "POST":
        name = pdcode.pdcode_name
        pdcode.delete()
        messages.success(request, f"PDcode '{pdcode_code}' deleted successfully.")
        return redirect("pdcodes:pdcodes", company_id=company.company_id)

    return render(
        request,
        "pdcodes/delete.html",
        {"pdcode": pdcode, "company": company, "company_id":company_id, "country": country, "country_slug":country_slug},
    )