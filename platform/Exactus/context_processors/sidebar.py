def sidebar_context(request):
    """
    Provides safe defaults for all sidebar variables so templates never fail.
    """

    vars = [
        "country",
        "country_slug",
        "company",
        "employee",
        "regulation",
        "regulation_id",
        "element",
        "element_code",
        "pdcode",
        "pdcode_code",
        "calculationbase",
        "payregister_id",
        "payroll_id",
    ]

    ctx = {var: request.resolver_match.kwargs.get(var, None)
           if request.resolver_match else None
           for var in vars}
    
    ctx['has_employee_context'] = bool(
    ctx.get('employee') and getattr(ctx['employee'], 'id', None)
)

    # For URLs that pass company_id instead of company
    if request.resolver_match:
        company_id = request.resolver_match.kwargs.get("company_id")
        if company_id and not ctx["company"]:
            from Exactus.company.models import Company
            ctx["company"] = Company.objects.filter(company_id=company_id).first()

    return ctx
