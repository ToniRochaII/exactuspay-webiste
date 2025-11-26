# elements/utils/csv_importer.py
import csv
from typing import Tuple, List

from Exactus.country.models import Country
from Exactus.elements.models import Element


def _to_bool(value, default=False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    val = str(value).strip().lower()
    if val in ("true", "t", "yes", "y", "1"):
        return True
    if val in ("false", "f", "no", "n", "0", ""):
        return False
    return default


def _to_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def import_elements_from_csv(
    csv_file, country: Country | None = None, dry_run: bool = False
) -> Tuple[int, int, List[str]]:
    """
    Import elements from a CSV file.

    Args:
        csv_file: file-like object or StringIO (already decoded text)
        country: if provided, all rows are imported for this country.
                 if None, CSV must have a 'country_code' column that
                 matches Country.iso2_code.
        dry_run: if True, validate and count but DO NOT save to the DB.

    Returns:
        (success_count, error_count, errors)
    """
    reader = csv.DictReader(csv_file)
    success_count = 0
    error_count = 0
    errors: List[str] = []

    for row_num, row in enumerate(reader, start=2):  # start=2 to account for header row
        try:
            # ----- Resolve country -----
            country_code = (row.get("country_code") or "").strip()

            if country is not None:
                element_country = country
            elif country_code:
                # IMPORTANT: your Country model uses iso2_code
                element_country = Country.objects.filter(
                    iso2_code=country_code
                ).first()
                if not element_country:
                    error_count += 1
                    errors.append(
                        f"Row {row_num}: Country with ISO2 code '{country_code}' not found"
                    )
                    continue
            else:
                error_count += 1
                errors.append(f"Row {row_num}: No country specified")
                continue

            # ----- Basic element identity -----
            element_code = (row.get("element_code") or "").strip()
            if not element_code:
                error_count += 1
                errors.append(f"Row {row_num}: Missing 'element_code'")
                continue

            # Check if element already exists
            existing_element = Element.objects.filter(
                country=element_country, element_code=element_code
            ).first()

            # ----- Build data dict -----
            element_data = {
                "country": element_country,
                "element_code": element_code,
                "element_name": row.get("element_name", "").strip(),
                "element_description": row.get("element_description", "").strip(),
                # Choices – ensure defaults match your model choices exactly
                "element_status": (row.get("element_status") or "Visible").strip()
                or None,
                "element_account": _to_int(row.get("element_account")),
                "element_map_code": _to_int(row.get("element_map_code")),
                "element_gl_account": _to_int(row.get("element_gl_account")),
                "element_frequency": (
                    row.get("element_frequency") or "Recurring"
                ).strip()
                or None,
                "element_type": (row.get("element_type") or "Regular").strip() or None,
                "element_class": (row.get("element_class") or "Statutory").strip()
                or None,
                "element_category": (row.get("element_category") or "Deduction").strip()
                or None,
                # Boolean flags
                "element_taxable": _to_bool(row.get("element_taxable"), default=False),
                "element_tax_flat": _to_bool(
                    row.get("element_tax_flat"), default=False
                ),
                "element_tax_irregular": _to_bool(
                    row.get("element_tax_irregular"), default=False
                ),
                "element_social_securitable": _to_bool(
                    row.get("element_social_securitable"), default=False
                ),
                "element_pensionable": _to_bool(
                    row.get("element_pensionable"), default=False
                ),
                "element_payable": _to_bool(row.get("element_payable"), default=True),
                "element_calculate": _to_bool(
                    row.get("element_calculate"), default=True
                ),
                "element_categorytype": (
                    row.get("element_categorytype") or "Bracketable"
                ).strip()
                or None,
                "archive": (row.get("archive") or "N").strip() or "N",
            }

            # ----- Save or simulate (dry run) -----
            if dry_run:
                # Just pretend we saved it successfully
                success_count += 1
                continue

            if existing_element:
                # Update existing element
                for field, value in element_data.items():
                    if field == "country":
                        continue  # don't reassign FK here
                    setattr(existing_element, field, value)
                existing_element.save()
            else:
                # Create new element
                Element.objects.create(**element_data)

            success_count += 1

        except Exception as e:
            error_count += 1
            errors.append(f"Row {row_num}: {str(e)}")

    return success_count, error_count, errors
