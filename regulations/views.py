# Exactus/views_regulations.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from country.models import Country
from .models import Regulations
from .forms import RegulationsForm


# ────────────────────────────────────────────────────────────────
# LIST REGULATIONS
# ────────────────────────────────────────────────────────────────
@login_required
def regulations(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    regulations = Regulations.objects.filter(country=country).order_by("-effective_date")
    return render(
        request,
        "regulations/index.html",
        {"country": country, "regulations": regulations, "country_slug":country.slug},
    )


# ────────────────────────────────────────────────────────────────
# CREATE REGULATION
# ────────────────────────────────────────────────────────────────
@login_required
def regulations_create(request, country_slug):
    """
    Create a new regulation for a specific country.
    """
    country = get_object_or_404(Country, slug=country_slug)

    if request.method == "POST":
        form = RegulationsForm(request.POST)
        if form.is_valid():
            regulation = form.save(commit=False)
            regulation.country = country
            regulation.save()
            messages.success(
                request,
                f"Regulation for {country.name} ({regulation.fiscal_year}) created successfully.",
            )
            return redirect("regulations:regulations", country_slug=country.slug)
    else:
        form = RegulationsForm()

    return render(
        request,
        "regulations/create.html",
        {"form": form, "country": country, "country_slug":country_slug},
    )


# ────────────────────────────────────────────────────────────────
# EDIT REGULATION
# ────────────────────────────────────────────────────────────────
@login_required
def regulations_edit(request, country_slug, regulations_id):
    country = get_object_or_404(Country, slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)

    if request.method == "POST":
        form = RegulationsForm(request.POST, instance=regulations)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Regulation for {country.name} ({regulations.fiscal_year}) updated successfully.",
            )
            return redirect("regulations", country_slug=country.slug)
    else:
        form = RegulationsForm(instance=regulations)

    return render(
        request,
        "regulations/edit.html",
        {"form": form, "country": country, "regulations": regulations, "country_slug":country_slug},
    )


# ──────────────────────

@login_required
def regulations_delete(request, country_slug, regulations_id):

    country = get_object_or_404(Country, slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)

    if request.method == "POST":
        year = regulations.fiscal_year
        regulations.delete()
        messages.success(request, f"Regulation for {country.name} ({year}) deleted successfully.")
        return redirect("regulations", country_slug=country.slug)

    return render(
        request,
        "regulations/delete.html",
        {"regulations": regulations, "country": country, "country_slug":country_slug},
    )




