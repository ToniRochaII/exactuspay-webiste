from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .utils.decorators import role_required
from .models import Country
from .forms import CountryForm


# ────────────────────────────────────────────────
# 🧩 Helper (Fix)
# ────────────────────────────────────────────────
def is_admin(user):
    """Return True if user is ADMIN based on the main User model."""
    return hasattr(user, "role") and user.role == "ADMIN"


# ────────────────────────────────────────────────
# 🌍 Country Pages
# ────────────────────────────────────────────────

@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def country(request):
    """Show active countries only."""
    countries = Country.objects.filter(archive="N").order_by("name")
    return render(request, "country/index.html", {"countries": countries})


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def country_delete(request):
    """Show archived (deleted) countries only."""
    countries = Country.objects.filter(archive="Y").order_by("name")
    return render(request, "country/delete.html", {"countries": countries})


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def country_create(request):
    """Create a new country."""
    if request.method == "POST":
        form = CountryForm(request.POST)
        if form.is_valid():
            country = form.save()
            messages.success(request, f"{country.name} created successfully.")
            return redirect("country:country")
    else:
        form = CountryForm()

    return render(request, "country/create.html", {"form": form})


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def country_edit(request, slug):
    """Edit a country."""
    country = get_object_or_404(Country, slug=slug)

    if request.method == "POST":
        form = CountryForm(request.POST, instance=country)
        if form.is_valid():
            form.save()
            messages.success(request, f"{country.name} updated successfully.")
            return redirect("country:country")
    else:
        form = CountryForm(instance=country)

    return render(request, "country/edit.html", {"form": form, "country": country, "country_slug": country.slug,})



