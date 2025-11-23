import csv
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any
from io import StringIO
from django.db import transaction


# ---------------------------------------------------------
# CONFIG OBJECTS
# ---------------------------------------------------------

@dataclass
class ForeignKeyMapping:
    csv_column: str              # CSV column name
    model_field: str             # Field name in the target model
    target_model: Any            # Django model class
    target_lookup: str           # Field to use for lookup in FK model


@dataclass
class ModelImportConfig:
    model: Any                                    # Django model class
    natural_key_fields: List[str]                 # Fields used for update_or_create
    field_mapping: Dict[str, str]                 # CSV column → model field
    fk_mappings: List[ForeignKeyMapping] = field(default_factory=list)
    validator: Optional[Callable[[Dict[str, str]], None]] = None


# ---------------------------------------------------------
# COUNTRY IMPORT CONFIGURATION
# ---------------------------------------------------------

from country.models import Country


def validate_country_row(row):
    """Strict validation rules for Country imports."""

    if len(row.get("iso2_code", "")) != 2:
        raise ValueError("iso2_code must be exactly 2 characters")

    if len(row.get("iso3_code", "")) != 3:
        raise ValueError("iso3_code must be exactly 3 characters")

    if row.get("status") not in ["ACTIVE", "IMPLEMENTING", "INACTIVE"]:
        raise ValueError(f"Invalid status '{row.get('status')}'")

    if row.get("numbering_format") not in ["1,000.00", "1.000,00"]:
        raise ValueError("Invalid numbering format")

    if row.get("currency_position") not in ["BEFORE", "AFTER"]:
        raise ValueError("Invalid currency_position")

    if row.get("date_format") not in [
        "DD/MM/YYYY", "MM/DD/YYYY", "YYYY/MM/DD", "YYYY/DD/MM"
    ]:
        raise ValueError("Invalid date_format")

    if row.get("archive") not in ["Y", "N"]:
        raise ValueError("archive must be 'Y' or 'N'")


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
        fk_mappings=[],  # No FKs in Country
        validator=validate_country_row
    ),
}


# ---------------------------------------------------------
# MAIN IMPORT FUNCTION
# ---------------------------------------------------------

def import_from_csv(model_key: str, file_obj, dry_run: bool = False):
    """
    Universal CSV importer for ExactusPay.

    Args:
        model_key (str): key from IMPORT_CONFIGS
        file_obj: Django UploadedFile or file-like object
        dry_run (bool): validate only, do not save changes

    Returns:
        dict: {created, updated, errors}
    """

    # Validate model key
    if model_key not in IMPORT_CONFIGS:
        raise ValueError(f"Unknown import key '{model_key}'")

    config = IMPORT_CONFIGS[model_key]
    model = config.model

    # Convert Django UploadedFile -> text buffer
    if hasattr(file_obj, "read"):
        text = file_obj.read().decode("utf-8-sig")  # supports BOM
        file_obj = StringIO(text)

    reader = csv.DictReader(file_obj)

    created = 0
    updated = 0
    errors = []

    @transaction.atomic
    def run_import():
        nonlocal created, updated

        for line_num, row in enumerate(reader, start=2):  # line 1 = header
            try:
                # -------------------------
                # VALIDATION
                # -------------------------
                if config.validator:
                    config.validator(row)

                attrs = {}

                # -------------------------
                # SIMPLE FIELD MAPPINGS
                # -------------------------
                for csv_col, model_field in config.field_mapping.items():
                    raw_value = row.get(csv_col)
                    if raw_value not in [None, ""]:
                        attrs[model_field] = raw_value

                # -------------------------
                # FOREIGN KEYS
                # -------------------------
                for fk in config.fk_mappings:
                    raw_value = row.get(fk.csv_column)
                    if raw_value:
                        target_obj = fk.target_model.objects.get(
                            **{fk.target_lookup: raw_value}
                        )
                        attrs[fk.model_field] = target_obj

                # -------------------------
                # UPDATE OR CREATE
                # -------------------------
                lookup_kwargs = {
                    key: attrs[key]
                    for key in config.natural_key_fields
                    if key in attrs
                }

                defaults = {
                    key: value
                    for key, value in attrs.items()
                    if key not in config.natural_key_fields
                }

                obj, created_flag = model.objects.update_or_create(
                    **lookup_kwargs,
                    defaults=defaults
                )

                created += int(created_flag)
                updated += int(not created_flag)

            except Exception as e:
                errors.append({
                    "line": line_num,
                    "row": row,
                    "error": str(e)
                })

        # -------------------------
        # DRY RUN ROLLBACK
        # -------------------------
        if dry_run:
            transaction.set_rollback(True)

    run_import()

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
    }
