from __future__ import annotations

from types import SimpleNamespace

from django.utils.translation import gettext as _


_DICT_KEYS_TO_TRANSLATE = {
    "title",
    "body",
    "label",
    "value",
    "note",
    "subtitle",
}


def _translate_value(value):
    if isinstance(value, str):
        return _(value)
    if isinstance(value, list):
        return [_translate_value(item) for item in value]
    if isinstance(value, dict):
        translated = {}
        for key, item in value.items():
            if key in _DICT_KEYS_TO_TRANSLATE or isinstance(item, (list, dict)):
                translated[key] = _translate_value(item)
            else:
                translated[key] = item
        return translated
    return value


def localize_country(country):
    translated_country_name = _translate_value(country.country_name)
    localized_seo_title = _translate_value(country.seo_title)
    default_seo_suffix = " Payroll Guide | Country Payroll Intelligence | ExactusPay"
    if country.seo_title and country.seo_title.endswith(default_seo_suffix):
        localized_seo_title = _("%(country_name)s Payroll Guide | Country Payroll Intelligence | ExactusPay") % {
            "country_name": translated_country_name,
        }

    return SimpleNamespace(
        slug=country.slug,
        iso_code=country.iso_code,
        country_name=translated_country_name,
        official_name=_translate_value(country.official_name),
        hero_intro=_translate_value(country.hero_intro),
        overview=_translate_value(country.overview),
        flag_url=country.flag_url,
        capital=_translate_value(country.capital),
        primary_languages=_translate_value(country.primary_languages),
        currency=_translate_value(country.currency),
        population_display=_translate_value(country.population_display),
        timezones=_translate_value(country.timezones),
        dialing_code=_translate_value(country.dialing_code),
        date_format=_translate_value(country.date_format),
        internet_domain=_translate_value(country.internet_domain),
        payroll_frequency=_translate_value(country.payroll_frequency),
        pay_currency=_translate_value(country.pay_currency),
        tax_year=_translate_value(country.tax_year),
        standard_working_week=_translate_value(country.standard_working_week),
        public_holiday_count=_translate_value(country.public_holiday_count),
        statutory_elements=_translate_value(country.statutory_elements),
        employer_contribution_summary=_translate_value(country.employer_contribution_summary),
        termination_notice_summary=_translate_value(country.termination_notice_summary),
        minimum_wage_summary=_translate_value(country.minimum_wage_summary),
        seo_title=localized_seo_title,
        meta_description=_translate_value(country.meta_description),
        meta_keywords=_translate_value(country.meta_keywords),
        last_reviewed_on=country.last_reviewed_on,
    )


def localized_fact_items(country):
    translated = localize_country(country)
    items = [
        {"label": _("Official country name"), "value": translated.official_name},
        {"label": _("Capital"), "value": translated.capital},
        {"label": _("Main language(s)"), "value": translated.primary_languages},
        {"label": _("Currency"), "value": translated.currency},
        {"label": _("Population"), "value": translated.population_display},
        {"label": _("Time zone(s)"), "value": translated.timezones},
        {"label": _("International dialling code"), "value": translated.dialing_code},
        {"label": _("Date format"), "value": translated.date_format},
        {"label": _("Internet domain"), "value": translated.internet_domain},
    ]
    return [item for item in items if item["value"]]


def localized_payroll_intelligence(country):
    translated = localize_country(country)
    items = [
        {"label": _("Payroll frequency"), "value": translated.payroll_frequency},
        {"label": _("Typical pay currency"), "value": translated.pay_currency},
        {"label": _("Tax year"), "value": translated.tax_year},
        {"label": _("Standard working week"), "value": translated.standard_working_week},
        {"label": _("Public holiday count"), "value": translated.public_holiday_count},
        {"label": _("Common statutory elements"), "value": translated.statutory_elements},
        {"label": _("Employer contribution summary"), "value": translated.employer_contribution_summary},
        {"label": _("Termination / notice highlights"), "value": translated.termination_notice_summary},
        {"label": _("Minimum wage indicator"), "value": translated.minimum_wage_summary},
    ]
    static_items = [item for item in items if item["value"]]
    dynamic_items = _translate_value(country.payroll_data_points or [])
    return static_items + list(dynamic_items)


def localized_nested_content(value):
    return _translate_value(value)
