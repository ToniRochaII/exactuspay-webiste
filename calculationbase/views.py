from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from country.models import Country
from regulations.models import Regulations
from elements.models import Element
from .models import CalculationBase
from .forms import CalculationBaseForm


@login_required
def calculationbase_list(request, country_slug, regulations_id):
    country = get_object_or_404(Country, country_slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)

    bases = CalculationBase.objects.filter(
        country=country, regulations=regulations
    ).select_related("element", "element_base")

    return render(
        request,
        "calculationbase/index.html",
        {"country": country, "regulations": regulations, "bases": bases, "country_slug":country_slug},
    )


@login_required
def calculationbase_create(request, country_slug, regulations_id):
    country = get_object_or_404(Country, country_slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)

    if request.method == "POST":
        form = CalculationBaseForm(request.POST, country=country, regulations=regulations)
        if form.is_valid():
            cb = form.save(commit=False)
            cb.country = country
            cb.regulations = regulations
            cb.save()
            messages.success(request, "Calculation Base created successfully.")
            return redirect("calculationbase:calculationbase_list", country_slug=country_slug, regulations_id=regulations_id)
    else:
        form = CalculationBaseForm(country=country, regulations=regulations)

    return render(request, "calculationbase/form.html", {"form": form, "country": country, "regulations": regulations, "country_slug":country_slug})


@login_required
def calculationbase_edit(request, country_id, pk):
    country = get_object_or_404(Country, pk=country_id)
    regulations = get_object_or_404(Regulations, country=country)
    cb = get_object_or_404(CalculationBase, pk=pk, country=country, regulations=regulations)

    if request.method == "POST":
        form = CalculationBaseForm(request.POST, instance=cb, country=country)
        if form.is_valid():
            form.save()
            messages.success(request, "Calculation Base updated successfully.")
            return redirect("calculationbase:calculationbase_list", country_id=country.id, regulations_id=regulations.id)
    else:
        form = CalculationBaseForm(instance=cb, country=country)

    return render(
        request,
        "calculationbase/form.html",
        {"form": form, "country": country, "regulations": regulations},
    )


@login_required
def calculationbase_delete(request, country_id, regulations_id, pk):
    country = get_object_or_404(Country, pk=country_id)
    regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)
    cb = get_object_or_404(CalculationBase, pk=pk, country=country, regulations=regulations)

    if request.method == "POST":
        cb.delete()
        messages.success(request, "Calculation Base deleted successfully.")
        return redirect("calculationbase:list", country_id=country.id, regulations_id=regulations.id)

    return render(
        request,
        "calculationbase/delete.html",
        {"cb": cb, "country": country, "regulations": regulations},
    )
