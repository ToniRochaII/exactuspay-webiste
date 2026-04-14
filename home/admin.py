from django.contrib import admin

from .models import DemoRequest


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ("company", "first_name", "last_name", "email", "employees", "region", "created_at")
    list_filter = ("employees", "region", "created_at")
    search_fields = ("company", "first_name", "last_name", "email")
    ordering = ("-created_at",)
