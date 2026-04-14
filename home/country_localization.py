from __future__ import annotations

from types import SimpleNamespace

from django.utils.translation import get_language, gettext as _


_DICT_KEYS_TO_TRANSLATE = {
    "title",
    "body",
    "label",
    "value",
    "note",
    "subtitle",
}


_COUNTRY_NAME_MAP = {
    "ar": {
        "AO": "أنغولا",
        "AR": "الأرجنتين",
        "BR": "البرازيل",
        "CL": "تشيلي",
        "CR": "كوستاريكا",
        "ET": "إثيوبيا",
        "GB": "المملكة المتحدة",
        "NG": "نيجيريا",
        "NL": "هولندا",
        "PK": "باكستان",
        "EG": "مصر",
        "IN": "الهند",
        "ID": "إندونيسيا",
        "MA": "المغرب",
        "PA": "بنما",
        "PE": "بيرو",
        "PH": "الفلبين",
        "SA": "المملكة العربية السعودية",
        "ZA": "جنوب أفريقيا",
        "TR": "تركيا",
        "AE": "الإمارات العربية المتحدة",
    },
    "de": {
        "AO": "Angola",
        "AR": "Argentinien",
        "BR": "Brasilien",
        "CL": "Chile",
        "CR": "Costa Rica",
        "ET": "Äthiopien",
        "GB": "Vereinigtes Königreich",
        "NG": "Nigeria",
        "NL": "Niederlande",
        "PK": "Pakistan",
        "EG": "Ägypten",
        "IN": "Indien",
        "ID": "Indonesien",
        "MA": "Marokko",
        "PA": "Panama",
        "PE": "Peru",
        "PH": "Philippinen",
        "SA": "Saudi-Arabien",
        "ZA": "Südafrika",
        "TR": "Türkei",
        "AE": "Vereinigte Arabische Emirate",
    },
    "es": {
        "AO": "Angola",
        "AR": "Argentina",
        "BR": "Brasil",
        "CL": "Chile",
        "CR": "Costa Rica",
        "ET": "Etiopía",
        "GB": "Reino Unido",
        "NG": "Nigeria",
        "NL": "Países Bajos",
        "PK": "Pakistán",
        "EG": "Egipto",
        "IN": "India",
        "ID": "Indonesia",
        "MA": "Marruecos",
        "PA": "Panamá",
        "PE": "Perú",
        "PH": "Filipinas",
        "SA": "Arabia Saudita",
        "ZA": "Sudáfrica",
        "TR": "Turquía",
        "AE": "Emiratos Árabes Unidos",
    },
    "fr": {
        "AO": "Angola",
        "AR": "Argentine",
        "BR": "Brésil",
        "CL": "Chili",
        "CR": "Costa Rica",
        "ET": "Éthiopie",
        "GB": "Royaume-Uni",
        "NG": "Nigéria",
        "NL": "Pays-Bas",
        "PK": "Pakistan",
        "EG": "Égypte",
        "IN": "Inde",
        "ID": "Indonésie",
        "MA": "Maroc",
        "PA": "Panama",
        "PE": "Pérou",
        "PH": "Philippines",
        "SA": "Arabie saoudite",
        "ZA": "Afrique du Sud",
        "TR": "Turquie",
        "AE": "Émirats arabes unis",
    },
    "id": {
        "AO": "Angola",
        "AR": "Argentina",
        "BR": "Brasil",
        "CL": "Chili",
        "CR": "Kosta Rika",
        "ET": "Etiopia",
        "GB": "Inggris Raya",
        "NG": "Nigeria",
        "NL": "Belanda",
        "PK": "Pakistan",
        "EG": "Mesir",
        "IN": "India",
        "ID": "Indonesia",
        "MA": "Maroko",
        "PA": "Panama",
        "PE": "Peru",
        "PH": "Filipina",
        "SA": "Arab Saudi",
        "ZA": "Afrika Selatan",
        "TR": "Turki",
        "AE": "Uni Emirat Arab",
    },
    "it": {
        "AO": "Angola",
        "AR": "Argentina",
        "BR": "Brasile",
        "CL": "Cile",
        "CR": "Costa Rica",
        "ET": "Etiopia",
        "GB": "Regno Unito",
        "NG": "Nigeria",
        "NL": "Paesi Bassi",
        "PK": "Pakistan",
        "EG": "Egitto",
        "IN": "India",
        "ID": "Indonesia",
        "MA": "Marocco",
        "PA": "Panama",
        "PE": "Perù",
        "PH": "Filippine",
        "SA": "Arabia Saudita",
        "ZA": "Sudafrica",
        "TR": "Turchia",
        "AE": "Emirati Arabi Uniti",
    },
    "pl": {
        "AO": "Angola",
        "AR": "Argentyna",
        "BR": "Brazylia",
        "CL": "Chile",
        "CR": "Kostaryka",
        "ET": "Etiopia",
        "GB": "Wielka Brytania",
        "NG": "Nigeria",
        "NL": "Niderlandy",
        "PK": "Pakistan",
        "EG": "Egipt",
        "IN": "Indie",
        "ID": "Indonezja",
        "MA": "Maroko",
        "PA": "Panama",
        "PE": "Peru",
        "PH": "Filipiny",
        "SA": "Arabia Saudyjska",
        "ZA": "Republika Południowej Afryki",
        "TR": "Turcja",
        "AE": "Zjednoczone Emiraty Arabskie",
    },
    "pt": {
        "AO": "Angola",
        "AR": "Argentina",
        "BR": "Brasil",
        "CL": "Chile",
        "CR": "Costa Rica",
        "ET": "Etiópia",
        "GB": "Reino Unido",
        "NG": "Nigéria",
        "NL": "Países Baixos",
        "PK": "Paquistão",
        "EG": "Egito",
        "IN": "Índia",
        "ID": "Indonésia",
        "MA": "Marrocos",
        "PA": "Panamá",
        "PE": "Peru",
        "PH": "Filipinas",
        "SA": "Arábia Saudita",
        "ZA": "África do Sul",
        "TR": "Turquia",
        "AE": "Emirados Árabes Unidos",
    },
    "ru": {
        "AO": "Ангола",
        "AR": "Аргентина",
        "BR": "Бразилия",
        "CL": "Чили",
        "CR": "Коста-Рика",
        "ET": "Эфиопия",
        "GB": "Великобритания",
        "NG": "Нигерия",
        "NL": "Нидерланды",
        "PK": "Пакистан",
        "EG": "Египет",
        "IN": "Индия",
        "ID": "Индонезия",
        "MA": "Марокко",
        "PA": "Панама",
        "PE": "Перу",
        "PH": "Филиппины",
        "SA": "Саудовская Аравия",
        "ZA": "Южная Африка",
        "TR": "Турция",
        "AE": "Объединенные Арабские Эмираты",
    },
    "sw": {
        "AO": "Angola",
        "AR": "Argentina",
        "BR": "Brazil",
        "CL": "Chile",
        "CR": "Costa Rica",
        "ET": "Ethiopia",
        "GB": "Ufalme wa Muungano",
        "NG": "Nigeria",
        "NL": "Uholanzi",
        "PK": "Pakistan",
        "EG": "Misri",
        "IN": "India",
        "ID": "Indonesia",
        "MA": "Moroko",
        "PA": "Panama",
        "PE": "Peru",
        "PH": "Ufilipino",
        "SA": "Saudi Arabia",
        "ZA": "Afrika Kusini",
        "TR": "Uturuki",
        "AE": "Falme za Kiarabu",
    },
    "th": {
        "AO": "แองโกลา",
        "AR": "อาร์เจนตินา",
        "BR": "บราซิล",
        "CL": "ชิลี",
        "CR": "คอสตาริกา",
        "ET": "เอธิโอเปีย",
        "GB": "สหราชอาณาจักร",
        "NG": "ไนจีเรีย",
        "NL": "เนเธอร์แลนด์",
        "PK": "ปากีสถาน",
        "EG": "อียิปต์",
        "IN": "อินเดีย",
        "ID": "อินโดนีเซีย",
        "MA": "โมร็อกโก",
        "PA": "ปานามา",
        "PE": "เปรู",
        "PH": "ฟิลิปปินส์",
        "SA": "ซาอุดีอาระเบีย",
        "ZA": "แอฟริกาใต้",
        "TR": "ตุรกี",
        "AE": "สหรัฐอาหรับเอมิเรตส์",
    },
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
    translated_country_name = _localized_country_name(country)
    localized_seo_title = _translate_value(country.seo_title)
    default_seo_suffix = " Payroll Guide | Country Payroll Intelligence | ExactusPay"
    if country.seo_title and country.seo_title.endswith(default_seo_suffix):
        localized_seo_title = _("%(country_name)s Payroll Guide | Country Payroll Intelligence | ExactusPay") % {
            "country_name": translated_country_name,
        }

    translated = SimpleNamespace(
        slug=country.slug,
        iso_code=country.iso_code,
        country_name=translated_country_name,
        official_name=_translate_value(country.official_name),
        flag_inline_svg=country.flag_inline_svg,
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
        meta_keywords=_translate_value(country.meta_keywords),
        last_reviewed_on=country.last_reviewed_on,
    )

    generated_intro = _build_country_intro(translated)
    generated_overview = _build_country_overview(translated)
    meta_description = generated_intro or generated_overview or _translate_value(country.meta_description)

    return SimpleNamespace(
        **translated.__dict__,
        hero_intro=generated_intro or _translate_value(country.hero_intro),
        overview=generated_overview or generated_intro or _translate_value(country.overview) or _translate_value(country.hero_intro),
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
    return _collect_pairs(
        (_("Payroll frequency"), translated.payroll_frequency),
        (_("Typical pay currency"), translated.pay_currency),
        (_("Tax year"), translated.tax_year),
        (_("Standard working week"), translated.standard_working_week),
    )[:3]


def localized_glance_cards(country):
    translated = localize_country(country)
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
    return _collect_pairs(
        (_("Payroll frequency"), translated.payroll_frequency),
        (_("Tax year"), translated.tax_year),
        (_("Employer contribution summary"), translated.employer_contribution_summary),
        (_("Termination / notice highlights"), translated.termination_notice_summary),
    )[:4]
