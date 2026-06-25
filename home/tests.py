import ast
import html
import json
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail


from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from accounts.models import Profile
from home.context_processors import site_context
from home.country_catalog import get_country_catalog
from home.country_localization_data import (
    COUNTRY_NAME_MAP,
    OFFICIAL_NAME_MAP,
    REGION_NAME_MAP,
)
from home.models import CountryProfile, DemoRequest

User = get_user_model()


TRANSLATION_AUDIT_ALLOWLIST = {
    "ExactusPay",
    "Euro (EUR)",
}


def _localized_path(locale: str, path: str) -> str:
    path = re.sub(r"^/[a-z]{2}(?=/|$)", "", path) or "/"
    return f"/{locale}{path}" if path != "/" else f"/{locale}/"


def _public_locale_codes() -> list[str]:
    return [
        language["code"]
        for language in site_context(None)["public_languages"]
        if language["code"] != settings.LANGUAGE_CODE
    ]


def _route_inventory() -> list[str]:
    with translation.override(settings.LANGUAGE_CODE):
        routes = [
            reverse("home:home"),
            reverse("home:country_hub"),
            reverse("home:features"),
            reverse("home:platform"),
            reverse("home:security"),
            reverse("home:demo"),
            reverse("home:brazil_article_0001"),
            reverse("home:brazil_article_0002"),
            reverse("home:brazil_article_0003"),
            reverse("home:brazil_article_0004"),
            reverse("home:brazil_article_0005"),
            reverse("home:chile_article_0001"),
            reverse("home:costa_rica_article_0001"),
            reverse("accounts:login"),
            reverse("accounts:register"),
        ]
        routes.extend(
            reverse("home:country_detail", kwargs={"slug": country.slug})
            for country in get_country_catalog()
        )
    return routes


def _should_audit_msgid(msgid: str) -> bool:
    if msgid in _translation_audit_exemptions():
        return False
    if "%(" in msgid or "{{" in msgid or "{%" in msgid:
        return False
    if not re.search(r"[A-Za-z]", msgid):
        return False
    if len(msgid) < 4 and " " not in msgid:
        return False
    if re.fullmatch(r"[A-Z0-9+./:&()'’ -]+", msgid):
        return False
    return True


def _entry_msgstr(entry: str) -> str | None:
    parts: list[str] = []
    collecting = False

    for line in entry.splitlines():
        if line.startswith("msgstr "):
            collecting = True
            parts = [ast.literal_eval(line[7:])]
            continue
        if collecting and line.startswith('"'):
            parts.append(ast.literal_eval(line))
            continue
        if collecting:
            break

    if not collecting:
        return None
    return "".join(parts)


@lru_cache(maxsize=None)
def _translation_audit_exemptions() -> frozenset[str]:
    exemptions = set(TRANSLATION_AUDIT_ALLOWLIST)
    exemptions.update(
        country.capital
        for country in get_country_catalog()
        if getattr(country, "capital", "")
    )
    return frozenset(exemptions)


@lru_cache(maxsize=None)
def _untranslated_msgids(locale: str) -> tuple[str, ...]:
    locale_path = (
        Path(settings.BASE_DIR) / "locale" / locale / "LC_MESSAGES" / "django.po"
    )
    text = locale_path.read_text(encoding="utf-8")
    entries = re.split(r"\n\n(?=#:|#,|msgid )", text)
    msgids = []

    for entry in entries:
        msgid_match = re.search(r'^msgid "(.*)"$', entry, re.M)
        if not msgid_match:
            continue
        msgid = msgid_match.group(1)
        if not _should_audit_msgid(msgid):
            continue
        if _entry_msgstr(entry) == "":
            msgids.append(msgid)

    return tuple(sorted(set(msgids), key=len, reverse=True))


class PublicPageTests(TestCase):
    def test_core_pages_are_available(self):
        routes = [
            reverse("home:home"),
            reverse("home:country_hub"),
            reverse("home:country_detail", kwargs={"slug": "brazil"}),
            reverse("home:features"),
            reverse("home:platform"),
            reverse("home:security"),
            reverse("home:demo"),
            reverse("home:brazil_article_0001"),
            reverse("home:brazil_article_0002"),
            reverse("home:brazil_article_0003"),
            reverse("home:brazil_article_0004"),
            reverse("home:brazil_article_0005"),
            reverse("home:chile_article_0001"),
            reverse("home:costa_rica_article_0001"),
            reverse("accounts:login"),
            reverse("accounts:register"),
        ]

        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)

    def test_localised_route_is_available(self):
        response = self.client.get("/pt/features/")
        self.assertEqual(response.status_code, 200)

    def test_country_page_uses_catalog_country_data(self):
        response = self.client.get(
            reverse("home:country_detail", kwargs={"slug": "brazil"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Brazil")
        self.assertContains(response, "/static/img/flags/br.png")
        self.assertContains(response, "Secretariat of the Federal Revenue of Brazil")

    def test_localized_country_page_uses_translated_tax_year_and_generated_copy(self):
        response = self.client.get("/pt/countries/united-kingdom/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "6 de abril a 5 de abril")

    def test_localized_catalog_country_page_renders_authority_content(self):
        response = self.client.get("/pt/countries/ireland/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Revenue Commissioners")
        self.assertContains(response, "Department of Social Protection")

    def test_country_hub_includes_curated_footprint(self):
        response = self.client.get(reverse("home:country_hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "54")
        self.assertContains(response, "angola")
        self.assertContains(response, "brazil")
        self.assertContains(response, "ireland")
        self.assertContains(response, "poland")
        self.assertContains(response, "united-kingdom")
        self.assertContains(response, "united-arab-emirates")

    def test_poland_country_page_uses_catalog_country_data(self):
        response = self.client.get(
            reverse("home:country_detail", kwargs={"slug": "poland"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/img/flags/pl.png")
        self.assertContains(response, "National Revenue Administration (KAS)")
        self.assertContains(response, "Social Insurance Institution (ZUS)")

    def test_united_kingdom_country_page_uses_catalog_country_data(self):
        response = self.client.get(
            reverse("home:country_detail", kwargs={"slug": "united-kingdom"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/img/flags/gb.png")
        self.assertContains(response, "HM Revenue &amp; Customs (HMRC)")

    def test_portuguese_homepage_uses_corrected_locale_strings(self):
        response = self.client.get("/pt/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Português")
        self.assertContains(response, '<option value="es"')
        self.assertContains(response, "50+ países")
        self.assertContains(response, "Agendar demonstração")
        self.assertNotContains(response, "Suporte em português 24/7")
        self.assertNotContains(response, "mais de 40 países")
        self.assertNotContains(response, "Software de Folha Global")
        self.assertNotContains(response, "Spanish")

    def test_portuguese_country_hub_uses_corrected_filter_labels(self):
        response = self.client.get("/pt/countries/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Buscar países")
        self.assertContains(response, "Região")
        self.assertContains(response, "Todas as regiões")
        self.assertContains(response, "Limpar filtros")
        self.assertContains(response, "Nenhum perfil de país encontrado")

    def test_arabic_country_hub_localizes_country_rows_and_regions(self):
        response = self.client.get("/ar/countries/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "دليل رواتب الدول")
        self.assertContains(response, "أستراليا")
        self.assertContains(response, "كومنولث أستراليا")
        self.assertContains(response, "أمريكا الجنوبية")
        self.assertContains(response, "آسيا والمحيط الهادئ")
        self.assertNotContains(response, "Commonwealth of Australia")
        self.assertNotContains(response, "South America")
        self.assertNotContains(response, "Asia-Pacific")

    def test_country_localization_maps_cover_all_public_locales(self):
        country_codes = {country.iso_code for country in get_country_catalog()}
        region_names = {country.region for country in get_country_catalog()}

        for locale in _public_locale_codes():
            with self.subTest(locale=locale, dataset="country_names"):
                self.assertEqual(country_codes - set(COUNTRY_NAME_MAP[locale]), set())
            with self.subTest(locale=locale, dataset="official_names"):
                self.assertEqual(country_codes - set(OFFICIAL_NAME_MAP[locale]), set())
            with self.subTest(locale=locale, dataset="regions"):
                self.assertEqual(region_names - set(REGION_NAME_MAP[locale]), set())

    def test_country_hub_uses_localized_catalog_data_for_all_public_locales(self):
        for locale in _public_locale_codes():
            response = self.client.get(f"/{locale}/countries/")
            rendered = html.unescape(response.content.decode("utf-8"))

            with self.subTest(locale=locale, field="status"):
                self.assertEqual(response.status_code, 200)
            with self.subTest(locale=locale, field="official_name"):
                self.assertIn(OFFICIAL_NAME_MAP[locale]["AU"], rendered)
                self.assertNotIn("Commonwealth of Australia", rendered)
            with self.subTest(locale=locale, field="region"):
                self.assertIn(REGION_NAME_MAP[locale]["Asia-Pacific"], rendered)

    def test_switzerland_country_page_localizes_shared_country_copy_for_all_public_locales(
        self,
    ):
        for locale in _public_locale_codes():
            response = self.client.get(f"/{locale}/countries/switzerland/")
            rendered = html.unescape(response.content.decode("utf-8"))

            with self.subTest(locale=locale, field="status"):
                self.assertEqual(response.status_code, 200)
            with self.subTest(locale=locale, field="verified_reference"):
                self.assertNotIn("Verified country reference", rendered)
            with self.subTest(locale=locale, field="profile_intro"):
                self.assertNotIn(
                    "This profile is designed as a practical employer reference.",
                    rendered,
                )
            with self.subTest(locale=locale, field="how_to_use"):
                self.assertNotIn(
                    "Use this profile as a first-pass employer reference",
                    rendered,
                )
            with self.subTest(locale=locale, field="payroll_intelligence"):
                self.assertNotIn(
                    "A structured view of the payroll details employers usually need first",
                    rendered,
                )
            with self.subTest(locale=locale, field="authority_labels"):
                self.assertNotIn("Tax authority", rendered)
                self.assertNotIn("Social security authority", rendered)
                self.assertNotIn("Payroll currency", rendered)
                self.assertNotIn("Coverage note", rendered)

    def test_language_switcher_renders_supported_language_codes(self):
        response = self.client.get(reverse("home:home"))
        expected_codes = [code for code, _label in settings.LANGUAGES]

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f"const supportedLanguageCodes = {json.dumps(expected_codes)}",
        )
        for language_code in expected_codes:
            with self.subTest(language_code=language_code):
                self.assertContains(response, f'<option value="{language_code}"')

    def test_localized_pages_do_not_show_default_english_nav_labels(self):
        response = self.client.get("/pt/")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Request Demo")
        self.assertNotContains(response, "Log In")
        self.assertNotContains(response, "Countries")


class TranslationAuditTests(TestCase):
    def test_public_locales_do_not_render_untranslated_source_strings(self):
        routes = _route_inventory()

        for locale in _public_locale_codes():
            untranslated = _untranslated_msgids(locale)
            for route in routes:
                localized_route = _localized_path(locale, route)
                with self.subTest(locale=locale, route=localized_route):
                    response = self.client.get(localized_route)
                    self.assertEqual(response.status_code, 200)

                    rendered = html.unescape(response.content.decode("utf-8"))
                    found = [msgid for msgid in untranslated if msgid in rendered][:20]
                    self.assertEqual(
                        found,
                        [],
                        msg=f"Untranslated strings found in {localized_route}: {found}",
                    )


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class DemoRequestTests(TestCase):
    def test_demo_request_is_saved_and_emailed(self):
        response = self.client.post(
            reverse("home:demo_request"),
            {
                "first_name": "Ana",
                "last_name": "Silva",
                "email": "ana@example.com",
                "company": "Exactus Labs",
                "employees": "50-250",
                "region": "LATAM",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("home:demo_thankyou"))
        self.assertEqual(DemoRequest.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertContains(response, "Thank you for your request")

    def test_demo_thankyou_requires_successful_submission(self):
        response = self.client.get(reverse("home:demo_thankyou"))
        self.assertRedirects(response, reverse("home:demo"))

    def test_invalid_demo_request_stays_on_demo_page(self):
        response = self.client.post(
            reverse("home:demo_request"),
            {"first_name": "Ana"},
            follow=True,
        )
        self.assertRedirects(response, reverse("home:demo"))
        self.assertEqual(DemoRequest.objects.count(), 0)


class AccountTests(TestCase):
    def test_profile_is_created_with_user(self):
        user = User.objects.create_user(username="tester", password="pass12345")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_user_can_register_and_edit_profile(self):
        register_response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "maria",
                "first_name": "Maria",
                "last_name": "Costa",
                "email": "maria@example.com",
                "password1": "ComplexPass123",
                "password2": "ComplexPass123",
            },
            follow=True,
        )

        self.assertEqual(register_response.status_code, 200)
        self.assertTrue(User.objects.filter(username="maria").exists())

        profile_response = self.client.post(
            reverse("accounts:profile"),
            {
                "first_name": "Maria",
                "last_name": "Costa",
                "email": "maria@example.com",
                "company_name": "ExactusPay",
                "job_title": "Operations Lead",
                "phone_number": "+44 20 1234 5678",
                "preferred_language": "pt",
                "timezone": "Europe/London",
                "notes": "Prefers Portuguese",
            },
            follow=True,
        )

        self.assertEqual(profile_response.status_code, 200)
        profile = User.objects.get(username="maria").profile
        self.assertEqual(profile.company_name, "ExactusPay")
        self.assertEqual(profile.preferred_language, "pt")
