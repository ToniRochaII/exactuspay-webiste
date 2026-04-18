from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Profile
from home.models import CountryProfile, DemoRequest

User = get_user_model()


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
        response = self.client.get(reverse("home:country_detail", kwargs={"slug": "brazil"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Brazil")
        self.assertContains(response, "/static/img/flags/br.png")
        self.assertContains(response, "Secretariat of the Federal Revenue of Brazil")

    def test_localized_country_page_uses_translated_tax_year_and_generated_copy(self):
        response = self.client.get("/th/countries/united-kingdom/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "6 เมษายน ถึง 5 เมษายน")

    def test_localized_catalog_country_page_renders_authority_content(self):
        response = self.client.get("/th/countries/ireland/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ireland")
        self.assertContains(response, "Revenue Commissioners")
        self.assertContains(response, "Department of Social Protection")

    def test_country_hub_includes_curated_footprint(self):
        response = self.client.get(reverse("home:country_hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "52")
        self.assertContains(response, "Angola")
        self.assertContains(response, "Brazil")
        self.assertContains(response, "Ireland")
        self.assertContains(response, "United Arab Emirates")


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

        self.assertRedirects(response, reverse("home:demo"))
        self.assertEqual(DemoRequest.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertContains(response, "Thank you!")


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
