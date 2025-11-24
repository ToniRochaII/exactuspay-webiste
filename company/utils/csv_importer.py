# company/utils/csv_importer.py
import csv
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any
from io import StringIO
from django.db import transaction
from country.models import Country
from company.models import Company

@dataclass
class ForeignKeyMapping:
    csv_column: str
    model_field: str
    target_model: Any
    target_lookup: str

@dataclass
class ModelImportConfig:
    model: Any
    natural_key_fields: List[str]
    field_mapping: Dict[str, str]
    fk_mappings: List[ForeignKeyMapping] = field(default_factory=list)
    validator: Optional[Callable[[Dict[str, str]], None]] = None

def validate_company_row(row):
    """Strict validation rules for Company imports."""
    
    # Validate required fields
    required_fields = ['country_code', 'company_code', 'trade_name', 'legal_name']
    for field in required_fields:
        if not row.get(field):
            raise ValueError(f"Missing required field: {field}")
    
    # Validate country exists
    country_code = row.get("country_code")
    if country_code:
        if not Country.objects.filter(iso2_code=country_code).exists():
            raise ValueError(f"Country with code '{country_code}' does not exist")
    
    # Validate account_status
    valid_statuses = ['ACTIVE', 'SUSPENDED', 'INACTIVE']
    account_status = row.get("account_status", "ACTIVE")
    if account_status not in valid_statuses:
        raise ValueError(f"Invalid account_status '{account_status}'. Must be one of: {', '.join(valid_statuses)}")
    
    # Validate account_archive
    valid_archive = ['Y', 'N']
    account_archive = row.get("account_archive", "N")
    if account_archive not in valid_archive:
        raise ValueError("account_archive must be 'Y' or 'N'")

IMPORT_CONFIGS = {
    "companies": ModelImportConfig(
        model=Company,
        natural_key_fields=["country", "company_code"],
        field_mapping={
            "country_code": "country",  # Handled by FK mapping
            "company_code": "company_code",
            "company_number": "company_number",
            "trade_name": "trade_name",
            "legal_name": "legal_name",
            "building_name": "building_name",
            "road_name_1": "road_name_1",
            "road_name_2": "road_name_2",
            "town": "town",
            "post_code": "post_code",
            "tax_id_1": "tax_id_1",
            "tax_id_2": "tax_id_2",
            "tax_id_3": "tax_id_3",
            "tax_id_4": "tax_id_4",
            "tax_id_5": "tax_id_5",
            "tax_id_6": "tax_id_6",
            "tax_id_7": "tax_id_7",
            "tax_id_8": "tax_id_8",
            "tax_id_9": "tax_id_9",
            "tax_id_10": "tax_id_10",
            "rti_user_id": "rti_user_id",
            "rti_password": "rti_password",
            "account_status": "account_status",
            "account_archive": "account_archive",
        },
        fk_mappings=[
            ForeignKeyMapping(
                csv_column="country_code",
                model_field="country",
                target_model=Country,
                target_lookup="iso2_code"
            )
        ],
        validator=validate_company_row
    ),
}

def import_from_csv(model_key: str, file_obj, dry_run: bool = False):
    """
    CSV importer for Companies.
    
    Args:
        model_key (str): key from IMPORT_CONFIGS
        file_obj: Django UploadedFile or file-like object
        dry_run (bool): validate only, do not save changes
    
    Returns:
        dict: {created, updated, errors}
    """

    if model_key not in IMPORT_CONFIGS:
        raise ValueError(f"Unknown import key '{model_key}'")

    config = IMPORT_CONFIGS[model_key]
    model = config.model

    # Convert Django UploadedFile -> text buffer
    if hasattr(file_obj, "read"):
        text = file_obj.read().decode("utf-8-sig")
        file_obj = StringIO(text)

    reader = csv.DictReader(file_obj)
    created = 0
    updated = 0
    errors = []

    @transaction.atomic
    def run_import():
        nonlocal created, updated

        for line_num, row in enumerate(reader, start=2):
            try:
                # Validation
                if config.validator:
                    config.validator(row)

                attrs = {}

                # Simple field mappings
                for csv_col, model_field in config.field_mapping.items():
                    # Skip FK fields for now
                    if any(fk.csv_column == csv_col for fk in config.fk_mappings):
                        continue
                    
                    raw_value = row.get(csv_col)
                    
                    # Handle empty values
                    if raw_value in [None, ""]:
                        continue
                    
                    attrs[model_field] = raw_value

                # Foreign Keys
                for fk in config.fk_mappings:
                    raw_value = row.get(fk.csv_column)
                    if raw_value:
                        try:
                            target_obj = fk.target_model.objects.get(
                                **{fk.target_lookup: raw_value}
                            )
                            attrs[fk.model_field] = target_obj
                        except fk.target_model.DoesNotExist:
                            raise ValueError(f"{fk.target_model.__name__} with {fk.target_lookup}='{raw_value}' not found")

                # Update or Create
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

        # Dry run rollback
        if dry_run:
            transaction.set_rollback(True)

    run_import()

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "dry_run": dry_run,
    }