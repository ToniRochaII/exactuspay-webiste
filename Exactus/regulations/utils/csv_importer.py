# regulations/utils/csv_importer.py
import csv
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any
from io import StringIO
from django.db import transaction
from Exactus.country.models import Country
from Exactus.regulations.models import Regulations  # Import from the correct location

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

# ⚠️ REMOVE THIS ENTIRE CLASS DEFINITION ⚠️
# class Regulations(models.Model):
#     country = models.ForeignKey("country.Country", on_delete=models.CASCADE, related_name="regulations")
#     fiscal_year = models.IntegerField()
#     effective_date = models.DateField()
#     slug = models.SlugField(unique=True, blank=True)
#     archive = models.CharField(
#         "Archive",
#         max_length=1,
#         choices=[("Y", "YES"), ("N", "NO")],
#         default="N",
#     )
# 
#     def save(self, *args, **kwargs):
#         # ... remove all this
# 
#     class Meta:
#         verbose_name = "Regulation"
#         verbose_name_plural = "Regulations"
#         ordering = ["country__name", "-fiscal_year"]
# 
#     def __str__(self):
#         return f"{self.country.name} - {self.fiscal_year}"

def validate_regulations_row(row):
    """Strict validation rules for Regulations imports."""
    
    # Validate country exists
    country_code = row.get("country_code")
    if country_code:
        if not Country.objects.filter(iso2_code=country_code).exists():
            raise ValueError(f"Country with code '{country_code}' does not exist")
    
    # Validate fiscal year
    fiscal_year = row.get("fiscal_year")
    if fiscal_year:
        try:
            year = int(fiscal_year)
            if year < 2000 or year > 2100:
                raise ValueError("Fiscal year must be between 2000 and 2100")
        except ValueError:
            raise ValueError("Fiscal year must be a valid number")
    
    # Validate effective_date format (basic check)
    effective_date = row.get("effective_date")
    if effective_date and len(effective_date) not in [8, 10]:
        raise ValueError("Effective date should be in YYYY-MM-DD format")
    
    # Validate archive field
    archive = row.get("archive", "N")
    if archive not in ["Y", "N"]:
        raise ValueError("Archive must be 'Y' or 'N'")

IMPORT_CONFIGS = {
    "regulations": ModelImportConfig(
        model=Regulations,  # This now references the model from regulations.models
        natural_key_fields=["country", "fiscal_year"],
        field_mapping={
            "country_code": "country",  # This will be handled by FK mapping
            "fiscal_year": "fiscal_year",
            "effective_date": "effective_date",
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
        validator=validate_regulations_row
    ),
}

def import_from_csv(model_key: str, file_obj, dry_run: bool = False):
    """
    CSV importer for Regulations.
    
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
                    if raw_value not in [None, ""]:
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

                # Convert fiscal_year to integer
                if "fiscal_year" in attrs:
                    attrs["fiscal_year"] = int(attrs["fiscal_year"])

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