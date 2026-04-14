import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("company_name", models.CharField(blank=True, max_length=150)),
                ("job_title", models.CharField(blank=True, max_length=120)),
                ("phone_number", models.CharField(blank=True, max_length=50)),
                ("preferred_language", models.CharField(choices=[("en", "English"), ("ar", "Arabic"), ("de", "German"), ("es", "Español"), ("fr", "French"), ("id", "Indonesian"), ("it", "Italian"), ("pl", "Polish"), ("pt", "Português"), ("ru", "Russian"), ("sw", "Swahili"), ("th", "Thai")], default="en", max_length=10)),
                ("timezone", models.CharField(default="UTC", max_length=64)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "profile", "verbose_name_plural": "profiles"},
        ),
    ]
