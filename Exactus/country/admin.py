from django.contrib import admin
from .models import Country

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "iso2_code",
        "iso3_code",
        "currency_code",
        "status",
        "decimals",
        "archive",
    )
    list_filter = ("status", "archive")
    search_fields = ("name", "iso2_code", "iso3_code", "currency_code")
    ordering = ("name",)
