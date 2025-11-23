import csv
from django.db import transaction
from django.apps import apps


def import_from_csv(file, model, field_map, required_fields=None, dry_run=False):
    """
    Universal CSV importer for all models.
    file: Uploaded file object (request.FILES["file"])
    model: Django model class (e.g. Country)
    field_map: {csv_column: model_field}
    required_fields: ["name", "code"]
    dry_run: If True → Validate but do not save
    """

    if required_fields is None:
        required_fields = []

    # Decode file if necessary
    file_data = file.read().decode("utf-8").splitlines()
    reader = csv.DictReader(file_data)

    created = 0
    updated = 0
    errors = []

    # Dry-run or real import is handled inside a transaction
    try:
        with transaction.atomic():
            for i, row in enumerate(reader, start=1):
                cleaned = {}

                # Validate required fields
                for field in required_fields:
                    if not row.get(field):
                        errors.append(f"Line {i}: Missing required field '{field}'")
                        continue

                # Build cleaned row
                for csv_col, model_field in field_map.items():
                    cleaned[model_field] = row.get(csv_col)

                # Unique lookup field (always 'code' for now)
                lookup_field = field_map.get("code", None)
                if lookup_field is None:
                    errors.append(f"Line {i}: No 'code' field in field_map")
                    continue

                lookup_value = cleaned.get(lookup_field)
                if not lookup_value:
                    errors.append(f"Line {i}: Missing code value")
                    continue

                # Get or create instance
                obj, created_flag = model.objects.update_or_create(
                    **{lookup_field: lookup_value},
                    defaults=cleaned
                )

                if created_flag:
                    created += 1
                else:
                    updated += 1

            # Rollback if dry-run
            if dry_run:
                raise Exception("DRY RUN - Rolling back changes")

    except Exception as e:
        if str(e) != "DRY RUN - Rolling back changes":
            errors.append(str(e))

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "dry_run": dry_run,
    }
