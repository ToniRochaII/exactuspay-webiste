from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse

from company.models import  Company 
from country.models import Country
from company.forms import CompanyForm
from .utils.decorators import role_required 


# ────────────────────────────────────────────────────────────────
# 🔍 Utility Functions
# ────────────────────────────────────────────────────────────────

def is_admin(user):
    """Helper: returns True if user has an Admin profile role."""
    return hasattr(user, "profile") and user.profile.role == "ADMIN"


# ────────────────────────────────────────────────────────────────
# 🧩 Company Pages
# ────────────────────────────────────────────────────────────────


@login_required
@role_required("ADMIN", "EXEC")
def company(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    companies = Company.objects.filter(country=country).order_by("trade_name")
    return render(request, "company/index.html", {"country": country, "companies": companies, "country_slug": country.slug})


@login_required
@role_required("ADMIN", "EXEC")
def company_create(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)


    if request.method == "POST":
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.country = country
            company.save()
            messages.success(request, f"Company '{company.trade_name}' added successfully.")
            return redirect("companies:company", country_slug=country.slug)
    else:
        form = CompanyForm()

    return render(
        request,
        "company/create.html",
        {"form": form, "country": country, "country_slug": country.slug}
    )



@login_required
@role_required("ADMIN", "EXEC")
def company_edit(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id, country=country)

    if request.method == "POST":
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect("companies:company", country_slug=country.slug)
    else:
        form = CompanyForm(instance=company)

    return render(request, "company/edit.html", {"form": form, "country": country, "country_slug":country_slug})


@login_required
@role_required("ADMIN", "EXEC")
def company_delete(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    companies = Company.objects.filter(country=country).order_by("trade_name")
    return render(request, "company/delete.html", {"country": country, "companies": companies, "country_slug": country.slug})






