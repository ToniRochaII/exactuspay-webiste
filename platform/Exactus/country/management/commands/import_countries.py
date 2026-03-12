from django.core.management.base import BaseCommand, CommandError
from utils.csv_importer import import_from_csv

class Command(BaseCommand):
    help = "Import Country CSV"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        path = options["csv_path"]
        dry_run = options["dry_run"]

        try:
            with open(path, "rb") as f:
                result = import_from_csv("country", f, dry_run=dry_run)
        except FileNotFoundError:
            raise CommandError("File not found")

        self.stdout.write(self.style.SUCCESS(
            f"Created: {result['created']}, Updated: {result['updated']}"
        ))

        if result["errors"]:
            self.stdout.write(self.style.WARNING("Errors:"))
            for error in result["errors"]:
                self.stdout.write(f"Line {error['line']}: {error['error']}")
