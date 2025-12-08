# Exactus/company/registry.py
from django import forms
import warnings

COMPANY_FORM_REGISTRY: dict[str, type[forms.ModelForm]] = {}


def register_company_form(country_code: str):
    """
    Decorator to register a country-specific CompanyForm.

    Usage:
        @register_company_form("BR")
        class CompanyFormBR(CompanyForm):
            ...
    """
    iso = country_code.upper().strip()

    def decorator(cls: type[forms.ModelForm]):
        if not issubclass(cls, forms.ModelForm):
            raise TypeError(
                f"@register_company_form('{iso}') can only be applied to ModelForm subclasses "
                f"(got: {cls.__name__})"
            )

        if iso in COMPANY_FORM_REGISTRY:
            warnings.warn(
                f"Overwriting existing CompanyForm registration for '{iso}'. "
                f"Old: {COMPANY_FORM_REGISTRY[iso].__name__}, New: {cls.__name__}",
                RuntimeWarning,
            )

        COMPANY_FORM_REGISTRY[iso] = cls
        return cls

    return decorator


def get_company_form_class(country) -> type[forms.ModelForm]:
    """
    Returns the registered CompanyForm subclass for the given country instance,
    or the base CompanyForm if none is registered.
    """
    from Exactus.company.forms import CompanyForm  # local import to avoid circular import

    if not country:
        return CompanyForm

    iso = (
        getattr(country, "iso2_code", None)
        or getattr(country, "iso2", None)
        or getattr(country, "code", None)
        or ""
    )

    iso = str(iso).upper().strip()
    return COMPANY_FORM_REGISTRY.get(iso, CompanyForm)
