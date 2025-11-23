from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from utils.decorators import role_required
from .models import PDcode
from company.models import Company
from country.models import Country
from .forms import PDcodeForm


# ─────────────────────────────────────────
# LIST
# ─────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def pdcode_list(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    pdcodes = PDcode.objects.order_by("pdcode_code").filter(company=company)

    return render(
        request,
        "pdcodes/index.html",
        {
            "country": country,
            "country_slug": country_slug,
            "company": company,
            "company_id": company_id,
            "pdcodes": pdcodes,
        },
    )


# ─────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def pdcode_create(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    pdcodes = PDcode.objects.order_by("pdcode_code").filter(company=company)

    if request.method == "POST":
        form = PDcodeForm(request.POST, company=company)
        if form.is_valid():
            pdcode = form.save(commit=False)
            pdcode.company = company
            pdcode.save()

            messages.success(
                request,
                f"PDcode '{pdcode.pdcode_code} – {pdcode.pdcode_name}' created successfully.",
            )
            return redirect(
                "pdcodes:pdcodes",
                country_slug=country_slug,
                company_id=company_id,
            )
    else:
        form = PDcodeForm(company=company)

    return render(
        request,
        "pdcodes/create.html",
        {
            "country": country,
            "country_slug": country_slug,
            "company": company,
            "company_id": company_id,
            "form": form,
            "pdcodes": pdcodes,
        },
    )


# ─────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def pdcode_edit(request, country_slug, company_id, pdcode_code):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    pdcode = get_object_or_404(PDcode, company=company, pdcode_code=pdcode_code)

    if request.method == "POST":
        form = PDcodeForm(request.POST, instance=pdcode, company=company)
        if form.is_valid():
            pdcode = form.save()
            messages.success(
                request,
                f"PDcode '{pdcode.pdcode_code} | {pdcode.pdcode_name}' updated successfully.",
            )
            return redirect(
                "pdcodes:pdcodes",
                country_slug=country_slug,
                company_id=company_id,
            )
    else:
        form = PDcodeForm(instance=pdcode, company=company)

    return render(
        request,
        "pdcodes/edit.html",
        {
            "country": country,
            "country_slug": country_slug,
            "company": company,
            "company_id": company_id,
            "pdcode": pdcode,
            "form": form,
        },
    )


# ─────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def pdcode_delete(request, country_slug, company_id, pdcode_code):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    pdcode = get_object_or_404(PDcode, company=company, pdcode_code=pdcode_code)

    if request.method == "POST":
        name = f"{pdcode.pdcode_code} – {pdcode.pdcode_name}"
        pdcode.delete()
        messages.success(request, f"PDcode '{name}' deleted successfully.")
        return redirect(
            "pdcodes:pdcodes",
            country_slug=country_slug,
            company_id=company_id,
        )

    return render(
        request,
        "pdcodes/delete.html",
        {
            "country": country,
            "country_slug": country_slug,
            "company": company,
            "company_id": company_id,
            "pdcode": pdcode,
        },
    )
