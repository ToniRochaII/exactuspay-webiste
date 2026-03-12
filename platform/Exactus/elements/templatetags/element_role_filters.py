from django import template
register = template.Library()

@register.filter
def has_role(user, roles):
    """Check if user's role is in a comma-separated list of roles."""
    if not user or not hasattr(user, "role"):
        return False
    role_list = [r.strip().upper() for r in roles.split(",")]
    return user.role.upper() in role_list

@register.filter
def get_tax_fields(form):
    """Get all tax-related fields from the form"""
    tax_field_names = [
        'element_taxable',
        'element_tax_flat',
        'element_tax_irregular',
        'element_social_securitable',
        'element_pensionable',
        'element_payable',
        'element_calculate'
    ]
    
    return [form[field_name] for field_name in tax_field_names if field_name in form.fields]