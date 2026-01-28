from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from Exactus.country.models import Country
from Exactus.regulations.models import Regulations
from Exactus.elements.models import Element
from Exactus.calculationbase.models import CalculationBase
from Exactus.calculationbase.forms import CalculationBaseForm


@login_required
def calculationbase_list(request, country_slug, regulations_id):
    country = get_object_or_404(Country, slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)

    bases = (
        CalculationBase.objects
        .filter(country=country, regulations=regulations)
        .select_related("element", "element_base")
    )

    return render(
        request,
        "calculationbase/index.html",
        {"country": country, "regulations": regulations, "bases": bases, "country_slug": country_slug},
    )


@login_required
def calculationbase_create(request, country_slug, regulations_id):
    country = get_object_or_404(Country, slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id)

    if request.method == "POST":
        form = CalculationBaseForm(request.POST, country=country, regulations=regulations)
        if form.is_valid():
            cb = form.save(commit=False)
            cb.country = country
            cb.regulations = regulations
            cb.save()
            messages.success(request, "Calculation Base created successfully.")
            return redirect(
                "calculationbase:list",
                country_slug=country.slug,
                regulations_id=regulations.id,
            )
    else:
        # --- FIX START: Set Default to 'Round down' ---
        initial_data = {
            'rounding_base': 'Round down',
            'rounding_taxed': 'Round down',
        }
        
        # Pre-fill defaults for all 16 bracket slots so they are ready when revealed by JS
        for i in range(16):
            suffix = f"{i:02d}"
            initial_data[f'round_bracket_logic_{suffix}'] = 'Round down'
            initial_data[f'round_result_logic_{suffix}'] = 'Round down'

        form = CalculationBaseForm(
            country=country, 
            regulations=regulations, 
            initial=initial_data
        )
        # --- FIX END ---

    bracket_range = [f"{i:02d}" for i in range(16)]

    return render(
        request,
        "calculationbase/form.html",
        {
            "form": form,
            "country": country,
            "regulations": regulations,
            "title": "Add Calculation Base",
            "country_slug": country_slug,
            "bracket_range": bracket_range,
        },
    )


@login_required
def calculationbase_edit(request, country_slug, regulations_id, pk):
    country = get_object_or_404(Country, slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)
    cb = get_object_or_404(CalculationBase, pk=pk, country=country, regulations=regulations)

    if request.method == "POST":
        form = CalculationBaseForm(request.POST, instance=cb, country=country, regulations=regulations)
        if form.is_valid():
            form.save()
            messages.success(request, "Calculation Base updated successfully.")
            return redirect(
                "calculationbase:list",
                country_slug=country.slug,
                regulations_id=regulations.id,
            )
    else:
        form = CalculationBaseForm(instance=cb, country=country, regulations=regulations)

    bracket_range = [f"{i:02d}" for i in range(16)]

    return render(
        request,
        "calculationbase/form.html",
        {
            "form": form,
            "country": country,
            "regulations": regulations,
            "title": "Edit Calculation Base",
            "country_slug": country_slug,
            "bracket_range": bracket_range,
        },
    )


@login_required
def calculationbase_delete(request, country_slug, regulations_id, pk):
    country = get_object_or_404(Country, slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)
    cb = get_object_or_404(CalculationBase, pk=pk, country=country, regulations=regulations)

    if request.method == "POST":
        cb.delete()
        messages.success(request, "Calculation Base deleted successfully.")
        return redirect(
            "calculationbase:list",
            country_slug=country.slug,
            regulations_id=regulations.id,
        )

    return render(
        request,
        "calculationbase/delete.html",
        {"cb": cb, "country": country, "regulations": regulations, "country_slug": country_slug},
    )