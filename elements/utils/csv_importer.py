# elements/utils/csv_importer.py
import csv
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any
from io import StringIO
from django.db import transaction
from country.models import Country
from elements.models import Element

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

def validate_element_row(row):
    """Strict validation rules for Element imports."""
    
    # Validate required fields
    required_fields = ['country_code', 'element_code', 'element_name', 'element_description']
    for field in required_fields:
        if not row.get(field):
            raise ValueError(f"Missing required field: {field}")
    
    # Validate country exists
    country_code = row.get("country_code")
    if country_code:
        if not Country.objects.filter(iso2_code=country_code).exists():
            raise ValueError(f"Country with code '{country_code}' does not exist")
    
    # Validate choice fields
    valid_status = ['Visible', 'Hidden']
    status = row.get("element_status")
    if status and status not in valid_status:
        raise ValueError(f"Invalid element_status '{status}'. Must be: {', '.join(valid_status)}")
    
    valid_frequency = ['Recurring', 'Non-recurring']
    frequency = row.get("element_frequency")
    if frequency and frequency not in valid_frequency:
        raise ValueError(f"Invalid element_frequency '{frequency}'. Must be: {', '.join(valid_frequency)}")
    
    valid_type = ['Regular', 'Irregular']
    element_type = row.get("element_type")
    if element_type and element_type not in valid_type:
        raise ValueError(f"Invalid element_type '{element_type}'. Must be: {', '.join(valid_type)}")
    
    valid_class = ['Standard', 'Statutory']
    element_class = row.get("element_class")
    if element_class and element_class not in valid_class:
        raise ValueError(f"Invalid element_class '{element_class}'. Must be: {', '.join(valid_class)}")
    
    valid_category = ['Payment', 'Deduction', 'Notional', 'Base', 'Gross up', 'ER Contribution', 'ER Cost']
    element_category = row.get("element_category")
    if element_category and element_category not in valid_category:
        raise ValueError(f"Invalid element_category '{element_category}'. Must be: {', '.join(valid_category)}")
    
    valid_categorytype = ['Bracketable', 'Prorational', 'Pension', 'Formulae', 'Base']
    element_categorytype = row.get("element_categorytype")
    if element_categorytype and element_categorytype not in valid_categorytype:
        raise ValueError(f"Invalid element_categorytype '{element_categorytype}'. Must be: {', '.join(valid_categorytype)}")
    
    # Validate numeric fields
    numeric_fields = ['element_account', 'element_map_code', 'element_gl_account']
    for field in numeric_fields:
        value = row.get(field)
        if value and value != "":
            try:
                int(value)
            except ValueError:
                raise ValueError(f"{field} must be a valid integer")
    
    # Validate boolean fields
    boolean_fields = [
        'element_taxable', 'element_tax_flat', 'element_tax_irregular',
        'element_social_securitable', 'element_pensionable', 'element_payable', 'element_calculate'
    ]
    for field in boolean_fields:
        value = row.get(field, "").upper()
        if value and value not in ['TRUE', 'FALSE', 'YES', 'NO', '1', '0', '']:
            raise ValueError(f"{field} must be TRUE/FALSE, YES/NO, or 1/0")
    
    # Validate archive
    archive = row.get("archive", "N")
    if archive not in ["Y", "N"]:
        raise ValueError("archive must be 'Y' or 'N'")

IMPORT_CONFIGS = {
    "elements": ModelImportConfig(
        model=Element,
        natural_key_fields=["country", "element_code"],
        field_mapping={
            "country_code": "country",  # Handled by FK mapping
            "element_code": "element_code",
            "element_description": "element_description",
            "element_name": "element_name",
            "element_status": "element_status",
            "element_account": "element_account",
            "element_map_code": "element_map_code",
            "element_gl_account": "element_gl_account",
            "element_frequency": "element_frequency",
            "element_type": "element_type",
            "element_class": "element_class",
            "element_category": "element_category",
            "element_taxable": "element_taxable",
            "element_tax_flat": "element_tax_flat",
            "element_tax_irregular": "element_tax_irregular",
            "element_social_securitable": "element_social_securitable",
            "element_pensionable": "element_pensionable",
            "element_payable": "element_payable",
            "element_calculate": "element_calculate",
            "element_categorytype": "element_categorytype",
            "archive": "archive",
        },
        fk_mappings=[
            ForeignKeyMapping(
                csv_column="country_code",
                model_field="country",
                target_model=Country,
                target_lookup="iso2_code"
            )
        ],
        validator=validate_element_row
    ),
}

def import_from_csv(model_key: str, file_obj, dry_run: bool = False):
    """
    CSV importer for Elements.
    
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
                    
                    # Convert boolean fields
                    if model_field in [
                        'element_taxable', 'element_tax_flat', 'element_tax_irregular',
                        'element_social_securitable', 'element_pensionable', 'element_payable', 'element_calculate'
                    ]:
                        if raw_value.upper() in ['TRUE', 'YES', '1']:
                            attrs[model_field] = True
                        elif raw_value.upper() in ['FALSE', 'NO', '0']:
                            attrs[model_field] = False
                    # Convert integer fields
                    elif model_field in ['element_account', 'element_map_code', 'element_gl_account']:
                        attrs[model_field] = int(raw_value)
                    else:
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