import csv
from io import TextIOWrapper


def clean_value(value):
    """Safely convert CSV cell values without executing code."""
    if value is None:
        return None

    value = str(value).strip()

    # Empty value → None
    if value == "":
        return None

    # Boolean conversion
    lowered = value.lower()
    if lowered in ["true", "yes", "1"]:
        return True
    if lowered in ["false", "no", "0"]:
        return False

    # Integer conversion
    if value.isdigit():
        return int(value)

    # Float conversion
    try:
        float_val = float(value)
        return float_val
    except ValueError:
        pass

    # Leave all other values as strings
    return value


def import_pdcodes_from_csv(
    file,
    company,
    field_map: dict,
    required_fields: list = None,
    dry_run: bool = False,
    update_existing: bool = True,
):
    """
    Generic CSV importer for PD Codes.
    - Performs safe value conversion (no eval)
    - Validates required fields
    - Creates or updates objects
    - Supports dry run mode
    """

    required_fields = required_fields or []
    result = {
        "created": 0,
        "updated": 0,
        "errors": [],
        "rows": [],
    }

    # Read CSV safely
    decoded = TextIOWrapper(file, encoding="utf-8")
    reader = csv.DictReader(decoded)

    from pdcodes.models import PDcode  # safe import inside function

    for row_number, row in enumerate(reader, start=2):  # header = row 1
        row_errors = []

        # Build PDcode data dict
        data = {}

        for csv_field, model_field in field_map.items():

            raw_value = row.get(csv_field, "").strip()

            cleaned = clean_value(raw_value)
            data[model_field] = cleaned

        # Validate required fields
        for req in required_fields:
            if not data.get(req):
                row_errors.append(f"Missing required field: {req}")

        if row_errors:
            result["errors"].append(
                f"Row {row_number}: " + "; ".join(row_errors)
            )
            continue

        # Check if PDcode exists
        existing = PDcode.objects.filter(
            company=company,
            pdcode_code=data.get("pdcode_code")
        ).first()

        if existing:
            if update_existing:
                # Update existing
                for k, v in data.items():
                    setattr(existing, k, v)
                if not dry_run:
                    try:
                        existing.save()
                    except Exception as e:
                        result["errors"].append(
                            f"Row {row_number}: failed to update — {str(e)}"
                        )
                        continue
                result["updated"] += 1
            else:
                result["rows"].append(
                    f"Row {row_number}: skipped (already exists)"
                )
            continue

        # Create new PDcode
        new_obj = PDcode(company=company, **data)

        if not dry_run:
            try:
                new_obj.save()
            except Exception as e:
                result["errors"].append(
                    f"Row {row_number}: failed to create — {str(e)}"
                )
                continue

        result["created"] += 1

    return result
