import csv
from io import TextIOWrapper

def import_from_csv(file, model, field_map, required_fields=None):
    """
    Generic CSV importer
    Args:
        file: Uploaded CSV file
        model: Django model class
        field_map: Dict mapping CSV headers → model field names
        required_fields: Optional list of fields that must exist
    Returns:
        (created, updated, errors)
    """
    created, updated, errors = 0, 0, []

    reader = csv.DictReader(TextIOWrapper(file, encoding='utf-8'))
    missing_fields = [f for f in required_fields or [] if f not in reader.fieldnames]
    if missing_fields:
        return (0, 0, [f"Missing fields: {', '.join(missing_fields)}"])

    for i, row in enumerate(reader, start=1):
        try:
            data = {field_map.get(k, k): v for k, v in row.items() if k in field_map}
            obj, created_flag = model.objects.update_or_create(
                **data,
            )
            if created_flag:
                created += 1
            else:
                updated += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")

    return (created, updated, errors)


from country.models import Country

IMPORT_CONFIGS = {
    "country": ModelImportConfig(
        model=Country,
        natural_key_fields=["iso2_code"],
        field_mapping={
            "iso2_code": "iso2_code",
            "iso3_code": "iso3_code",
            "name": "name",
            "status": "status",
            "official_language": "official_language",
            "currency_name": "currency_name",
            "currency_code": "currency_code",
            "fiscal_year_start": "fiscal_year_start",
            "fiscal_year_end": "fiscal_year_end",
            "numbering_format": "numbering_format",
            "currency_position": "currency_position",
            "date_format": "date_format",
            "decimals": "decimals",
            "archive": "archive",
        },
        fk_mappings=[]
    ),
}
