from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DemoRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_name", models.CharField(max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                ("email", models.EmailField(max_length=254)),
                ("company", models.CharField(max_length=150)),
                ("employees", models.CharField(choices=[("<50", "< 50"), ("50-250", "50-250"), ("250-1000", "250-1000"), ("1000+", "1000+")], max_length=20)),
                ("region", models.CharField(choices=[("Not sure yet", "Not sure yet"), ("LATAM", "LATAM"), ("Africa", "Africa"), ("Asia", "Asia"), ("Global", "Global")], default="Not sure yet", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
