from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Country, Element
from .forms import ElementForm


# ────────────────────────────────────────────────────────────────
# LIST ELEMENTS
# ────────────────────────────────────────────────────────────────
@login_required
def element(request, country_slug):
    """
    List all elements for a specific country.
    """
    country = get_object_or_404(Country, slug=country_slug)
    elements = Element.objects.filter(country=country).order_by("element_code")
    return render(
        request,
        "elements/index.html",
        {"country": country, "elements": elements, "country_slug":country_slug},
    )

# ────────────────────────────────────────────────────────────────
# CREATE ELEMENT
# ────────────────────────────────────────────────────────────────
@login_required
def element_create(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)

    form = ElementForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        element = form.save(commit=False)
        element.country = country
        element.save()

        messages.success(
            request,
            f"Element '{element.element_code} {element.element_name}' created successfully."
        )
        return redirect("elements:elements", country_slug=country.slug)

    return render(
        request,
        "elements/create.html",
        {
            "form": form,
            "country": country,
            "country_slug": country_slug,
        },
    )



# ────────────────────────────────────────────────────────────────
# EDIT ELEMENT
# ────────────────────────────────────────────────────────────────
@login_required
def element_edit(request, country_slug, element_code):
    """
    Edit an existing element.
    """
    country = get_object_or_404(Country, slug=country_slug)
    element = get_object_or_404(Element, element_code=element_code, country=country)

    if request.method == "POST":
        form = ElementForm(request.POST, instance=element)
        if form.is_valid():
            form.save()
            messages.success(request, f"Element '{element.element_code} | {element.element_name}' updated successfully.")
            return redirect("elements:elements", country_slug=country.slug)
    else:
        form = ElementForm(instance=element)

    return render(
        request,
        "elements/edit.html",
        {"form": form, "country": country, "element": element, "country_slug":country_slug},
    )


# ────────────────────────────────────────────────────────────────
# DELETE ELEMENT
# ────────────────────────────────────────────────────────────────
@login_required
def element_delete(request, country_slug, element_code):
    """
    Edit an existing element.
    """
    country = get_object_or_404(Country, slug=country_slug)
    element = get_object_or_404(Element, element_code=element_code, country=country)

    if request.method == "POST":
        name = element.element_name
        element.delete()
        messages.success(request, f"Element '{element_code}' deleted successfully.")
        return redirect("elements:elements", country_slug=country.slug)

    return render(
        request,
        "elements/delete.html",
        {"element": element, "country": country, "country_slug":country_slug},
    )





