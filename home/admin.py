from django.contrib import admin

from .models import CountryProfile, DemoRequest


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ("company", "first_name", "last_name", "email", "employees", "region", "created_at")
    list_filter = ("employees", "region", "created_at")
    search_fields = ("company", "first_name", "last_name", "email")
    ordering = ("-created_at",)


@admin.register(CountryProfile)
class CountryProfileAdmin(admin.ModelAdmin):
    list_display = ("country_name", "iso_code", "slug", "is_published", "sort_order", "last_reviewed_on")
    list_filter = ("is_published", "last_reviewed_on")
    search_fields = ("country_name", "official_name", "iso_code", "slug")
    ordering = ("sort_order", "country_name")
    prepopulated_fields = {"slug": ("country_name",)}
    fieldsets = (
        (
            "Identity",
            {
                "fields": (
                    "country_name",
                    "official_name",
                    "iso_code",
                    "slug",
                    "flag_media_path",
                    "is_published",
                    "sort_order",
                    "last_reviewed_on",
                )
            },
        ),
        (
            "SEO & hero",
            {
                "fields": (
                    "seo_title",
                    "meta_description",
                    "meta_keywords",
                    "hero_intro",
                    "overview",
                    "hero_highlights",
                    "glance_cards",
                )
            },
        ),
        (
            "Country facts",
            {
                "fields": (
                    "capital",
                    "primary_languages",
                    "currency",
                    "population_display",
                    "timezones",
                    "dialing_code",
                    "date_format",
                    "internet_domain",
                )
            },
        ),
        (
            "Payroll intelligence",
            {
                "fields": (
                    "payroll_frequency",
                    "pay_currency",
                    "tax_year",
                    "standard_working_week",
                    "public_holiday_count",
                    "statutory_elements",
                    "employer_contribution_summary",
                    "termination_notice_summary",
                    "minimum_wage_summary",
                    "payroll_data_points",
                )
            },
        ),
        (
            "Narrative sections",
            {
                "fields": (
                    "content_sections",
                    "employer_considerations",
                )
            },
        ),
    )
