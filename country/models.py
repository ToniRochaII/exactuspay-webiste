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
    model_field: str             # Field name in target model
    target_model: Any            # Django model class
    target_lookup: str           # Field to use for lookup in FK model


@dataclass
class ModelImportConfig:
    model: Any                                    # Django model
    natural_key_fields: List[str]                 # Fields used for update_or_create lookup
    field_mapping: Dict[str, str]                 # CSV → model field
    fk_mappings: List[ForeignKeyMapping] = field(default_factory=list)
    validator: Optional[Callable[[Dict[str, str]], None]] = None


# ---------------------------------------------------------
# IMPORT CONFIGS (example: Country ONLY right now)
# Add Company, Employee, Regulations, etc. later.
# ---------------------------------------------------------

from country.models import Country


def validate_country_row(row):
    """Optional: strict validation for Country import."""

    if len(row.get("iso2_code", "")) != 2:
        raise ValueError("iso2_code must be 2 characters")

    if len(row.get("iso3_code", "")) != 3:
        raise ValueError("iso3_code must be 3 characters")

    if row.get("status") not in ["ACTIVE", "IMPLEMENTING", "INACTIVE"]:
        raise ValueError(f"Invalid status '{row.get('status')}'")

    if row.get("numbering_format") not in ["1,000.00", "1.000,00"]:
        raise ValueError(f"Invalid numbering format '{row.get('numbering_format')}'")

    if row.get("currency_position") not in ["BEFORE", "AFTER"]:
        raise ValueError(f"Invalid currency_position '{row.get('currency_position')}'")

    if row.get("date_format") not in [
        "DD/MM/YYYY", "MM/DD/YYYY", "YYYY/MM/DD", "YYYY/DD/MM"
    ]:
        raise ValueError(f"Invalid date_format '{row.get('date_format')}'")

    if row.get("archive") not in ["Y", "N"]:
        raise ValueError("archive must be 'Y' or 'N'")


# Master configuration
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
        fk_mappings=[],        # Country has no FK fields
        validator=validate_country_row
    ),
}


# ---------------------------------------------------------
# MAIN IMPORT FUNCTION
# ---------------------------------------------------------

def import_from_csv(model_key: str, file_obj, dry_run: bool = False):
    """
    Generic CSV importer used for all modules in ExactusPay.

    Args:
        model_key (str): key used in IMPORT_CONFIGS
        file_obj (UploadedFile or file-like): the CSV file
        dry_run (bool): if True, validate only and rollback changes

    Returns:
        dict: {created, updated, errors}
    """

    if model_key not in IMPORT_CONFIGS:
        raise ValueError(f"Unknown model key '{model_key}'")

    config = IMPORT_CONFIGS[model_key]
    model = config.model

    # -----------------------------------------------------
    # Convert Django UploadedFile → text buffer
    # -----------------------------------------------------
    if hasattr(file_obj, "read"):
        text = file_obj.read().decode("utf-8-sig")  # supports BOM
        file_obj = StringIO(text)

    reader = csv.DictReader(file_obj)

    created = 0
    updated = 0
    errors = []

    # -----------------------------------------------------
    # Use atomic transaction so dry_run can rollback safely
    # -----------------------------------------------------
    @transaction.atomic
    def process():
        nonlocal created, updated

        for line_num, row in enumerate(reader, start=2):  # start=2 = header is line 1
            try:
                # -----------------------------------------
                # VALIDATION
                # -----------------------------------------
                if config.validator:
                    config.validator(row)

                attrs = {}

                # -----------------------------------------
                # SIMPLE FIELD MAPPINGS
                # -----------------------------------------
                for csv_col, model_field in config.field_mapping.items():
                    raw_value = row.get(csv_col)
                    if raw_value not in [None, ""]:
                        attrs[model_field] = raw_value

                # -----------------------------------------
                # FOREIGN KEYS
                # -----------------------------------------
                for fk in config.fk_mappings:
                    raw_value = row.get(fk.csv_column)
                    if raw_value:
                        target_obj = fk.target_model.objects.get(
                            **{fk.target_lookup: raw_value}
                        )
                        attrs[fk.model_field] = target_obj

                # -----------------------------------------
                # UPDATE OR CREATE
                # -----------------------------------------
                lookup_kwargs = {
                    field: attrs[field]
                    for field in config.natural_key_fields
                    if field in attrs
                }

                defaults = {
                    k: v for k, v in attrs.items()
                    if k not in config.natural_key_fields
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

        # -----------------------------------------
        # DRY RUN → Rollback everything
        # -----------------------------------------
        if dry_run:
            transaction.set_rollback(True)

    process()

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
    }
