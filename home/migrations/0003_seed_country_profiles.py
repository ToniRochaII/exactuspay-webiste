from datetime import date

from django.db import migrations


def seed_country_profiles(apps, schema_editor):
    CountryProfile = apps.get_model("home", "CountryProfile")

    profiles = [
        {
            "slug": "brazil",
            "iso_code": "BR",
            "country_name": "Brazil",
            "official_name": "Federative Republic of Brazil",
            "hero_intro": "A high-volume payroll market where monthly control, statutory accuracy, and clean reporting discipline matter from the first cycle.",
            "overview": "ExactusPay positions Brazil as a control-heavy payroll market: one monthly rhythm, multiple statutory layers, and strong demand for evidence-backed reporting. The country page format lets payroll, finance, and HR teams see the operating context quickly without switching between long guides and scattered data sources.",
            "flag_media_path": "flags/br.svg",
            "capital": "Brasilia",
            "primary_languages": "Portuguese",
            "currency": "Brazilian real (BRL)",
            "population_display": "203M+",
            "timezones": "UTC-05:00 to UTC-02:00",
            "dialing_code": "+55",
            "date_format": "DD/MM/YYYY",
            "internet_domain": ".br",
            "payroll_frequency": "Monthly",
            "pay_currency": "BRL",
            "tax_year": "Calendar year",
            "standard_working_week": "Up to 44 hours",
            "public_holiday_count": "National holidays plus state and municipal variations",
            "statutory_elements": "Common elements include INSS, FGTS, IRRF, paid vacation, and 13th salary handling.",
            "employer_contribution_summary": "Employer cost usually combines social security, FGTS funding, payroll taxes, and locally configured benefit costs.",
            "termination_notice_summary": "Notice handling, severance mechanics, and final-pay timing should be controlled carefully before termination goes live.",
            "minimum_wage_summary": "Maintain from the ExactusPay country data feed because it is time-sensitive.",
            "hero_highlights": [
                "Monthly payroll rhythm",
                "Heavy statutory layering",
                "Board-ready reporting need",
            ],
            "glance_cards": [
                {
                    "title": "Payroll control market",
                    "body": "Brazil rewards disciplined inputs, approval checkpoints, and strong payroll evidence trails.",
                    "icon": "fa-shield-halved",
                },
                {
                    "title": "Cost visibility first",
                    "body": "Employer-cost modelling matters before hiring, not only after the employee enters payroll.",
                    "icon": "fa-chart-line",
                },
                {
                    "title": "Local logic, global format",
                    "body": "ExactusPay keeps local payroll rules intact while translating outputs into one reporting standard.",
                    "icon": "fa-table-columns",
                },
            ],
            "payroll_data_points": [
                {
                    "label": "13th salary treatment",
                    "value": "Often planned as a dedicated year-end payroll event with separate controls and reporting.",
                },
                {
                    "label": "Typical employer focus",
                    "value": "Input quality, statutory timing, and reconciliation discipline across each payroll cycle.",
                },
            ],
            "content_sections": [
                {
                    "title": "Payroll overview",
                    "body": "Brazil payroll is usually managed on a monthly cadence with a dense statutory environment. Teams need reliable cut-offs, validated master data, and a clear route from local outputs to management reporting.",
                    "bullets": [
                        "Control changes before they hit live payroll.",
                        "Keep registers, approvals, and reconciliations aligned.",
                        "Translate local outputs into one executive reporting format.",
                    ],
                },
                {
                    "title": "Employment highlights",
                    "body": "Employers should align onboarding, salary setup, leave inputs, and variable pay capture early. First-cycle quality has an outsized effect on trust in the payroll process.",
                    "bullets": [
                        "Collect payroll-critical data before activation.",
                        "Map cost-centre and reporting ownership before scale increases.",
                    ],
                },
                {
                    "title": "Tax and social security summary",
                    "body": "Brazil typically requires close handling of income tax, social security, severance-fund mechanics, and related employer charges. ExactusPay treats these as structured payroll controls rather than ad hoc local adjustments.",
                    "bullets": [
                        "Keep statutory assumptions version-controlled.",
                        "Support review with traceable payroll evidence.",
                    ],
                },
                {
                    "title": "Compliance notes",
                    "body": "The commercial message on this page is not legal advice. It is a payroll operating view: where control is needed, where reporting often breaks, and where local precision needs to connect to one group standard.",
                },
            ],
            "employer_considerations": [
                "Plan employer-cost simulations before hiring approvals are finalised.",
                "Separate local payroll logic from executive reporting outputs.",
                "Build a repeatable process for changes, leave, and terminations.",
                "Review volatile indicators such as minimum wage in the live country data feed.",
            ],
            "seo_title": "Brazil Payroll Guide | Country Payroll Intelligence | ExactusPay",
            "meta_description": "Explore ExactusPay's reusable Brazil payroll page structure: employer facts, payroll intelligence, and country-level operating guidance in one scalable format.",
            "meta_keywords": "Brazil payroll, Brazil payroll guide, payroll in Brazil, employer cost Brazil, global payroll Brazil, ExactusPay Brazil",
            "sort_order": 10,
            "last_reviewed_on": date(2026, 4, 14),
        },
        {
            "slug": "chile",
            "iso_code": "CL",
            "country_name": "Chile",
            "official_name": "Republic of Chile",
            "hero_intro": "A payroll market where local registration, clean worker setup, and strong statutory evidence create a smoother route to scale.",
            "overview": "The ExactusPay Chile page balances commercial readability with operational relevance. It is structured for employers who need an at-a-glance country summary first, then a tighter payroll and compliance view when they move toward implementation.",
            "flag_media_path": "flags/cl.svg",
            "capital": "Santiago",
            "primary_languages": "Spanish",
            "currency": "Chilean peso (CLP)",
            "population_display": "19M+",
            "timezones": "UTC-04:00 with seasonal variation",
            "dialing_code": "+56",
            "date_format": "DD-MM-YYYY",
            "internet_domain": ".cl",
            "payroll_frequency": "Monthly",
            "pay_currency": "CLP",
            "tax_year": "Calendar year",
            "statutory_elements": "Pension, health, unemployment insurance, and local tax logic should be configured country by country.",
            "minimum_wage_summary": "Maintain from the ExactusPay country data feed because it is time-sensitive.",
            "hero_highlights": [
                "Monthly payroll structure",
                "Strong registration discipline",
                "Evidence-backed setup",
            ],
            "glance_cards": [
                {
                    "title": "Setup matters early",
                    "body": "Entity setup, worker registration, and payroll ownership boundaries shape the whole operating model.",
                    "icon": "fa-sitemap",
                },
                {
                    "title": "Country detail, one format",
                    "body": "Local payroll elements can still feed one ExactusPay reporting standard.",
                    "icon": "fa-layer-group",
                },
            ],
            "content_sections": [
                {
                    "title": "Payroll overview",
                    "body": "Chile is well suited to a structured implementation plan: establish registrations, confirm employing setup, then move into payroll controls and management reporting.",
                },
                {
                    "title": "Employer considerations",
                    "body": "The template is designed to accept richer payroll indicators over time while still rendering cleanly when only core data is available.",
                    "bullets": [
                        "Add market-specific contribution detail from the live data source.",
                        "Expand this page with ExactusPay implementation notes country by country.",
                    ],
                },
            ],
            "employer_considerations": [
                "Use country setup milestones before promising go-live dates.",
                "Keep payroll ownership explicit between local operations and HQ reporting.",
            ],
            "seo_title": "Chile Payroll Guide | Country Payroll Intelligence | ExactusPay",
            "meta_description": "Explore ExactusPay's Chile payroll page with employer facts, payroll intelligence, and a scalable country-page structure.",
            "meta_keywords": "Chile payroll, payroll in Chile, country payroll page, ExactusPay Chile",
            "sort_order": 20,
            "last_reviewed_on": date(2026, 4, 14),
        },
        {
            "slug": "costa-rica",
            "iso_code": "CR",
            "country_name": "Costa Rica",
            "official_name": "Republic of Costa Rica",
            "hero_intro": "A country page format built for employers who want a short, commercially clear summary before diving into payroll detail.",
            "overview": "Costa Rica demonstrates the fallback behaviour of the template: when a country has core metadata and a few operational notes, the page still reads cleanly and remains SEO-friendly while ExactusPay expands the underlying payroll dataset.",
            "flag_media_path": "flags/cr.svg",
            "capital": "San Jose",
            "primary_languages": "Spanish",
            "currency": "Costa Rican colon (CRC)",
            "population_display": "5M+",
            "timezones": "UTC-06:00",
            "dialing_code": "+506",
            "date_format": "DD/MM/YYYY",
            "internet_domain": ".cr",
            "payroll_frequency": "Monthly",
            "pay_currency": "CRC",
            "tax_year": "Calendar year",
            "hero_highlights": [
                "Expandable template",
                "Graceful data fallbacks",
                "Ready for more country feeds",
            ],
            "glance_cards": [
                {
                    "title": "Scales country by country",
                    "body": "The same template can support a lightly populated market or a data-rich payroll profile.",
                    "icon": "fa-expand",
                },
                {
                    "title": "Good for SEO",
                    "body": "Each country gets a dedicated URL, metadata, and structured long-form content blocks.",
                    "icon": "fa-magnifying-glass-chart",
                },
            ],
            "content_sections": [
                {
                    "title": "Payroll overview",
                    "body": "This profile shows how ExactusPay can publish a commercially strong country page even before every payroll data point is available from the platform feed.",
                },
                {
                    "title": "Compliance notes",
                    "body": "As richer country logic becomes available, the same sections can be filled with payroll and statutory detail without changing the page layout.",
                },
            ],
            "employer_considerations": [
                "Use this profile as the minimum viable country-page standard.",
                "Add live payroll metrics from the platform when they are ready.",
            ],
            "seo_title": "Costa Rica Payroll Guide | Country Payroll Intelligence | ExactusPay",
            "meta_description": "Explore ExactusPay's Costa Rica payroll page template with key country facts, payroll guidance, and scalable data fallbacks.",
            "meta_keywords": "Costa Rica payroll, payroll in Costa Rica, country payroll page, ExactusPay Costa Rica",
            "sort_order": 30,
            "last_reviewed_on": date(2026, 4, 14),
        },
    ]

    for payload in profiles:
        CountryProfile.objects.update_or_create(
            slug=payload["slug"],
            defaults=payload,
        )


def remove_country_profiles(apps, schema_editor):
    CountryProfile = apps.get_model("home", "CountryProfile")
    CountryProfile.objects.filter(slug__in=["brazil", "chile", "costa-rica"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0002_countryprofile"),
    ]

    operations = [
        migrations.RunPython(seed_country_profiles, remove_country_profiles),
    ]
