from django.utils.functional import SimpleLazyObject

def sidebar_context(request):
    """
    Main context processor for the entire application.
    Provides sidebar navigation data and context for all templates.
    """
    if not hasattr(request, "resolver_match") or not request.resolver_match:
        return {}

    kwargs = request.resolver_match.kwargs

    # ------------------------------------------
    # Helper to lazy-load objects only if needed
    # ------------------------------------------
    def load(model, key):
        """Safely returns a model instance or None."""
        pk = kwargs.get(key)
        if not pk:
            return None
        try:
            return model.objects.filter(pk=pk).first()
        except:
            return None

    # Import models locally (avoids circular imports)
    from Exactus.country.models import Country
    from Exactus.company.models import Company
    from Exactus.employee.models import Employee
    from Exactus.regulations.models import Regulations
    from Exactus.elements.models import Element
    from Exactus.pdcodes.models import PDcode
    from Exactus.calculationbase.models import CalculationBase
    from Exactus.payroll.models import Payroll

    # -----------------------------------------
    # Resolve objects (lazy evaluation)
    # -----------------------------------------
    context = {
        # Basic identifiers
        "country_slug": kwargs.get("country_slug"),
        "company_id": kwargs.get("company_id"),
        "employee_id": kwargs.get("employee_id"),
        "regulation_id": kwargs.get("regulation_id"),
        "element_code": kwargs.get("element_code"),
        "pdcode_code": kwargs.get("pdcode_code"),
        "payroll_id": kwargs.get("payroll_id"),
        
        # Lazy loaded objects
        "country": SimpleLazyObject(
            lambda: Country.objects.filter(slug=kwargs.get("country_slug")).first()
        ) if kwargs.get("country_slug") else None,

        "company": SimpleLazyObject(
            lambda: Company.objects.filter(company_id=kwargs.get("company_id")).first()
        ) if kwargs.get("company_id") else None,

        "employee": SimpleLazyObject(
            lambda: Employee.objects.filter(id=kwargs.get("employee_id")).first()
        ) if kwargs.get("employee_id") else None,

        "regulation": SimpleLazyObject(
            lambda: Regulations.objects.filter(regulations_id=kwargs.get("regulation_id")).first()
        ) if kwargs.get("regulation_id") else None,

        "element": SimpleLazyObject(
            lambda: Element.objects.filter(code=kwargs.get("element_code")).first()
        ) if kwargs.get("element_code") else None,

        "pdcode": SimpleLazyObject(
            lambda: PDcode.objects.filter(code=kwargs.get("pdcode_code")).first()
        ) if kwargs.get("pdcode_code") else None,

        "calculationbase": SimpleLazyObject(
            lambda: CalculationBase.objects.filter(pk=kwargs.get("pk")).first()
        ) if kwargs.get("pk") else None,
    }

    # -----------------------------------------
    # Computed helper flags
    # -----------------------------------------
    context["has_employee_context"] = bool(context["employee"])
    
    # For backward compatibility with templates that expect these
    # (This replaces the separate payroll_context function)
    if context["company"]:
        context["company"] = context["company"]  # Already set above
    if context["country"]:
        context["country"] = context["country"]  # Already set above

    return context

# Remove the duplicate payroll_context function or keep it if needed elsewhere
# def payroll_context(request):
#     # This is now redundant since sidebar_context handles it
#     return {}