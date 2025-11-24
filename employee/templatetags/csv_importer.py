# employee/utils/csv_importer.py
import csv
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any
from io import StringIO
from django.db import transaction
from company.models import Company
from employee.models import Employee

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

def validate_employee_row(row):
    """Strict validation rules for Employee imports."""
    
    # Validate required fields
    required_fields = ['company_code', 'employee_number', 'employee_code', 'employee_name', 'employee_surname']
    for field in required_fields:
        if not row.get(field):
            raise ValueError(f"Missing required field: {field}")
    
    # Validate company exists
    company_code = row.get("company_code")
    if company_code:
        if not Company.objects.filter(company_code=company_code).exists():
            raise ValueError(f"Company with code '{company_code}' does not exist")
    
    # Validate numeric fields
    numeric_fields = ['employee_number', 'employee_code']
    for field in numeric_fields:
        value = row.get(field)
        if value:
            try:
                int(value)
            except ValueError:
                raise ValueError(f"{field} must be a valid integer")
    
    # Validate gender
    valid_genders = ['Male', 'Female', '']
    gender = row.get("gender", "")
    if gender not in valid_genders:
        raise ValueError(f"Invalid gender '{gender}'. Must be Male, Female, or empty")
    
    # Validate marital status
    valid_marital_statuses = ['Single', 'Married', 'Divorced', '']
    marital_status = row.get("marital_status", "")
    if marital_status not in valid_marital_statuses:
        raise ValueError(f"Invalid marital_status '{marital_status}'. Must be Single, Married, Divorced, or empty")
    
    # Validate address type
    valid_address_types = ['Residential', 'Correspondence', '']
    address_type = row.get("employee_address_type", "")
    if address_type not in valid_address_types:
        raise ValueError(f"Invalid employee_address_type '{address_type}'. Must be Residential, Correspondence, or empty")

IMPORT_CONFIGS = {
    "employees": ModelImportConfig(
        model=Employee,
        natural_key_fields=["company", "employee_number"],
        field_mapping={
            "company_code": "company",  # Handled by FK mapping
            "employee_id": "employee_id",
            "employee_number": "employee_number",
            "employee_code": "employee_code",
            "employee_name": "employee_name",
            "employee_surname": "employee_surname",
            "gender": "gender",
            "date_of_birth": "date_of_birth",
            "marital_status": "marital_status",
            "employee_address_type": "employee_address_type",
            "employee_address_01": "employee_address_01",
            "employee_address_02": "employee_address_02",
            "employee_address_03": "employee_address_03",
            "employee_address_04": "employee_address_04",
            "employee_address_05": "employee_address_05",
            "employee_address_06": "employee_address_06",
            "employee_address_07": "employee_address_07",
            "bank_01": "bank_01",
            "bank_02": "bank_02",
            "bank_03": "bank_03",
            "bank_04": "bank_04",
            "bank_05": "bank_05",
            "bank_06": "bank_06",
            "bank_07": "bank_07",
            "bank_08": "bank_08",
            "bank_09": "bank_09",
            "bank_10": "bank_10",
            "department": "department",
            "cost_centre": "cost_centre",
            "job_title": "job_title",
            "position_number": "position_number",
            "fte": "fte",
            "tax_info_01": "tax_info_01",
            "tax_info_02": "tax_info_02",
            "tax_info_03": "tax_info_03",
            "tax_info_04": "tax_info_04",
            "tax_info_05": "tax_info_05",
            "tax_info_06": "tax_info_06",
            "tax_info_07": "tax_info_07",
        },
        fk_mappings=[
            ForeignKeyMapping(
                csv_column="company_code",
                model_field="company",
                target_model=Company,
                target_lookup="company_code"
            )
        ],
        validator=validate_employee_row
    ),
}

def import_from_csv(model_key: str, file_obj, dry_run: bool = False):
    """
    CSV importer for Employees.
    
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
                    
                    # Convert numeric fields
                    if model_field in ['employee_number', 'employee_code']:
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