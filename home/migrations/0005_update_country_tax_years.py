from django.db import migrations


COUNTRY_TAX_YEARS = {
    "angola": "1 January to 31 December",
    "argentina": "1 January to 31 December",
    "brazil": "1 January to 31 December",
    "chile": "1 January to 31 December",
    "costa-rica": "1 January to 31 December",
    "ethiopia": "8 July to 7 July",
    "united-kingdom": "6 April to 5 April",
    "nigeria": "1 January to 31 December",
    "netherlands": "1 January to 31 December",
    "pakistan": "1 July to 30 June",
    "egypt": "1 January to 31 December",
    "india": "1 April to 31 March",
    "indonesia": "1 January to 31 December",
    "morocco": "Typically 1 January to 31 December",
    "panama": "1 January to 31 December",
    "peru": "1 January to 31 December",
    "philippines": "1 January to 31 December for individual tax/payroll",
    "saudi-arabia": "Entity fiscal year; returns generally filed within 120 days after year-end",
    "south-africa": "1 March to 28/29 February",
    "turkey": "1 January to 31 December for individual tax",
    "united-arab-emirates": "Calendar year or the entity's 12-month financial reporting period",
}


def update_country_tax_years(apps, schema_editor):
    CountryProfile = apps.get_model("home", "CountryProfile")
    for slug, tax_year in COUNTRY_TAX_YEARS.items():
        CountryProfile.objects.filter(slug=slug).update(tax_year=tax_year)


def restore_country_tax_years(apps, schema_editor):
    CountryProfile = apps.get_model("home", "CountryProfile")
    CountryProfile.objects.filter(slug__in=COUNTRY_TAX_YEARS.keys()).update(tax_year="Calendar year")


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0004_expand_country_profiles"),
    ]

    operations = [
        migrations.RunPython(update_country_tax_years, restore_country_tax_years),
    ]
