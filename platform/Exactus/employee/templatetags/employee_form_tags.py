from django import template

register = template.Library()

@register.inclusion_tag('employee/includes/form_field.html')
def floating_field(field, col_class='col-md-4'):
    return {
        'field': field,
        'col_class': col_class,
    }


@register.simple_tag
def get_country_flag(country):
    """Returns flag emoji for country"""
    flags = {
        'brazil': '🇧🇷',
        'united-kingdom': '🇬🇧',
        'argentina': '🇦🇷',
    }
    return flags.get(country.slug, '🌐')


@register.filter
def has_field(form, field_name: str) -> bool:
    return hasattr(form, "fields") and field_name in form.fields
