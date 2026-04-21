from __future__ import annotations

from types import SimpleNamespace

from django.utils.translation import get_language, gettext as _

from .country_localization_data import (
    COUNTRY_NAME_MAP as _COUNTRY_NAME_MAP,
    OFFICIAL_NAME_MAP as _OFFICIAL_NAME_MAP,
    REGION_NAME_MAP as _REGION_NAME_MAP,
)


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


def _localized_country_name(country):
    language = (get_language() or "").split("-")[0]
    return _COUNTRY_NAME_MAP.get(language, {}).get(country.iso_code, _translate_value(country.country_name))


def _localized_official_name(country):
    language = (get_language() or "").split("-")[0]
    return _OFFICIAL_NAME_MAP.get(language, {}).get(country.iso_code, _translate_value(country.official_name))


def _localized_region(region):
    language = (get_language() or "").split("-")[0]
    return _REGION_NAME_MAP.get(language, {}).get(region, _translate_value(region))


def _format_pair(label, value):
    if not value:
        return ""
    return f"{label}: {value}"


def _collect_pairs(*items):
    return [_format_pair(label, value) for label, value in items if value]


def _join_sentences(items):
    clean_items = []
    for item in items:
        if not item:
            continue
        clean_items.append(item.rstrip("."))
    if not clean_items:
        return ""
    return ". ".join(clean_items) + "."


def _build_country_intro(translated):
    pairs = _collect_pairs(
        (_("Payroll frequency"), translated.payroll_frequency),
        (_("Typical pay currency"), translated.pay_currency),
        (_("Tax year"), translated.tax_year),
    )
    return _join_sentences(pairs)


def _build_country_overview(translated):
    facts = _collect_pairs(
        (_("Official country name"), translated.official_name),
        (_("Capital"), translated.capital),
        (_("Main language(s)"), translated.primary_languages),
        (_("Currency"), translated.currency),
    )
    payroll = _collect_pairs(
        (_("Payroll frequency"), translated.payroll_frequency),
        (_("Typical pay currency"), translated.pay_currency),
        (_("Tax year"), translated.tax_year),
    )
    return _join_sentences(facts[:2] + payroll[:2]) or _join_sentences(facts[:3]) or _join_sentences(payroll)


def localize_country(country):
    is_generated_catalog = getattr(country, "is_generated_catalog", False)
    translated_country_name = _localized_country_name(country)
    localized_seo_title = _translate_value(country.seo_title)
    default_seo_suffix = " Payroll Guide | Country Payroll Intelligence | ExactusPay"
    if country.seo_title and country.seo_title.endswith(default_seo_suffix):
        localized_seo_title = _("%(country_name)s Payroll Guide | Country Payroll Intelligence | ExactusPay") % {
            "country_name": translated_country_name,
        }
    elif is_generated_catalog and country.seo_title == f"{country.country_name} Payroll Guide | ExactusPay":
        localized_seo_title = _("%(country_name)s Payroll Guide | ExactusPay") % {
            "country_name": translated_country_name,
        }

    explicit_intro = _translate_value(country.hero_intro)
    if is_generated_catalog and country.hero_intro.startswith("ExactusPay's "):
        explicit_intro = _(
            "ExactusPay's %(country_name)s payroll guide is structured around verified authorities, core payroll references, and practical employer review points."
        ) % {"country_name": translated_country_name}

    explicit_overview = _translate_value(country.overview)
    if is_generated_catalog and country.overview.startswith("This ") and "verified employer reference points" in country.overview:
        explicit_overview = _(
            "This %(country_name)s payroll profile focuses on verified employer reference points. Where ExactusPay could confirm the main tax or social-security body, it is listed below. Fields without a reliable confirmation are intentionally left blank."
        ) % {"country_name": translated_country_name}

    explicit_meta_description = _translate_value(country.meta_description)
    if is_generated_catalog and country.meta_description.startswith("Explore ExactusPay's "):
        explicit_meta_description = _(
            "Explore ExactusPay's %(country_name)s payroll guide with verified authority mapping and core employer reference points."
        ) % {"country_name": translated_country_name}

    localized_meta_keywords = _translate_value(country.meta_keywords)
    if is_generated_catalog and country.meta_keywords.endswith(f", ExactusPay {country.country_name}"):
        localized_meta_keywords = _(
            "%(country_name)s payroll, %(country_name)s tax authority, %(country_name)s social security, ExactusPay %(country_name)s"
        ) % {"country_name": translated_country_name}

    translated = SimpleNamespace(
        slug=country.slug,
        is_generated_catalog=is_generated_catalog,
        iso_code=country.iso_code,
        country_name=translated_country_name,
        official_name=_localized_official_name(country),
        region=_localized_region(getattr(country, "region", "")),
        flag_inline_svg=country.flag_inline_svg,
        flag_inline_png=getattr(country, "flag_inline_png", ""),
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
        meta_keywords=localized_meta_keywords,
        tax_authority_name=_translate_value(getattr(country, "tax_authority_name", "")),
        social_security_authority_name=_translate_value(getattr(country, "social_security_authority_name", "")),
        authority_note=_translate_value(getattr(country, "authority_note", "")),
        last_reviewed_on=country.last_reviewed_on,
    )

    generated_intro = _build_country_intro(translated)
    generated_overview = _build_country_overview(translated)
    meta_description = explicit_meta_description or explicit_intro or explicit_overview or generated_intro or generated_overview

    return SimpleNamespace(
        **translated.__dict__,
        hero_intro=explicit_intro or generated_intro,
        overview=explicit_overview or explicit_intro or generated_overview or generated_intro,
        meta_description=meta_description,
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


def localized_hero_highlights(country):
    translated = localize_country(country)
    explicit_highlights = []
    if not getattr(country, "is_generated_catalog", False):
        explicit_highlights = _translate_value(getattr(country, "hero_highlights", []) or [])
    if explicit_highlights:
        return explicit_highlights
    return _collect_pairs(
        (_("Payroll frequency"), translated.payroll_frequency),
        (_("Typical pay currency"), translated.pay_currency),
        (_("Tax year"), translated.tax_year),
        (_("Standard working week"), translated.standard_working_week),
    )[:3]


def localized_glance_cards(country):
    translated = localize_country(country)
    explicit_cards = []
    if not getattr(country, "is_generated_catalog", False):
        explicit_cards = _translate_value(getattr(country, "glance_cards", []) or [])
    if explicit_cards:
        return explicit_cards
    return [
        {
            "title": _("Key facts"),
            "body": _join_sentences(
                _collect_pairs(
                    (_("Official country name"), translated.official_name),
                    (_("Capital"), translated.capital),
                    (_("Main language(s)"), translated.primary_languages),
                )[:3]
            ),
            "icon": "fa-earth-africa",
        },
        {
            "title": _("Payroll intelligence"),
            "body": _join_sentences(
                _collect_pairs(
                    (_("Payroll frequency"), translated.payroll_frequency),
                    (_("Typical pay currency"), translated.pay_currency),
                    (_("Tax year"), translated.tax_year),
                )[:3]
            ),
            "icon": "fa-layer-group",
        },
        {
            "title": _("Compliance notes"),
            "body": _join_sentences(
                _collect_pairs(
                    (_("Common statutory elements"), translated.statutory_elements),
                    (_("Employer contribution summary"), translated.employer_contribution_summary),
                    (_("Termination / notice highlights"), translated.termination_notice_summary),
                )[:3]
            ),
            "icon": "fa-shield-halved",
        },
    ]


def localized_content_sections(country):
    translated = localize_country(country)
    explicit_sections = []
    if not getattr(country, "is_generated_catalog", False):
        explicit_sections = _translate_value(getattr(country, "content_sections", []) or [])
    if explicit_sections:
        return explicit_sections
    return [
        {
            "title": _("Payroll overview"),
            "body": _join_sentences(
                _collect_pairs(
                    (_("Payroll frequency"), translated.payroll_frequency),
                    (_("Typical pay currency"), translated.pay_currency),
                    (_("Tax year"), translated.tax_year),
                )
            ),
            "bullets": _collect_pairs(
                (_("Date format"), translated.date_format),
                (_("Time zone(s)"), translated.timezones),
                (_("Internet domain"), translated.internet_domain),
            ),
        },
        {
            "title": _("Employment highlights"),
            "body": _join_sentences(
                _collect_pairs(
                    (_("Standard working week"), translated.standard_working_week),
                    (_("Public holiday count"), translated.public_holiday_count),
                    (_("Termination / notice highlights"), translated.termination_notice_summary),
                )
            ),
            "bullets": _collect_pairs(
                (_("Main language(s)"), translated.primary_languages),
                (_("International dialling code"), translated.dialing_code),
                (_("Population"), translated.population_display),
            ),
        },
        {
            "title": _("Tax and social security summary"),
            "body": _join_sentences(
                _collect_pairs(
                    (_("Common statutory elements"), translated.statutory_elements),
                    (_("Employer contribution summary"), translated.employer_contribution_summary),
                    (_("Minimum wage indicator"), translated.minimum_wage_summary),
                )
            ),
            "bullets": _collect_pairs(
                (_("Typical pay currency"), translated.pay_currency),
                (_("Tax year"), translated.tax_year),
            ),
        },
        {
            "title": _("Compliance notes"),
            "body": _join_sentences(
                _collect_pairs(
                    (_("Official country name"), translated.official_name),
                    (_("Capital"), translated.capital),
                    (_("Date format"), translated.date_format),
                )
            ),
            "bullets": _collect_pairs(
                (_("Main language(s)"), translated.primary_languages),
                (_("Time zone(s)"), translated.timezones),
                (_("Internet domain"), translated.internet_domain),
            ),
        },
    ]


def localized_employer_considerations(country):
    translated = localize_country(country)
    explicit_items = []
    if not getattr(country, "is_generated_catalog", False):
        explicit_items = _translate_value(getattr(country, "employer_considerations", []) or [])
    if explicit_items:
        return explicit_items
    return _collect_pairs(
        (_("Payroll frequency"), translated.payroll_frequency),
        (_("Tax year"), translated.tax_year),
        (_("Employer contribution summary"), translated.employer_contribution_summary),
        (_("Termination / notice highlights"), translated.termination_notice_summary),
    )[:4]
