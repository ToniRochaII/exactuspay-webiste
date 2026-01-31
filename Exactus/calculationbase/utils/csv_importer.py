# Exactus/calculationbase/utils/csv_importer.py

import csv
from decimal import Decimal, InvalidOperation
from django.db import transaction
from Exactus.country.models import Country
from Exactus.regulations.models import Regulations
from Exactus.elements.models import Element
from Exactus.calculationbase.models import CalculationBase

def import_calculationbase_from_csv(io_string, country=None, regulations=None, dry_run=False):
    """
    Imports CalculationBase records.
    - Local Mode: Pass 'country' and 'regulations' arguments.
    - Global Mode: Pass None; the script looks for 'country_code' and 'fiscal_year' columns.
    """
    reader = csv.DictReader(io_string)
    success_count = 0
    error_count = 0
    errors = []

    # Helper to clean strings
    def clean(val):
        return val.strip() if val else ""

    # Helper to parse decimals safely
    def parse_dec(val, default=0):
        if not val:
            return default
        try:
            return Decimal(val.replace(',', ''))
        except (InvalidOperation, ValueError):
            return default

    # Helper to parse integers safely
    def parse_int(val, default=0):
        if not val:
            return default
        try:
            return int(val)
        except ValueError:
            return default

    with transaction.atomic():
        if dry_run:
            sid = transaction.savepoint()

        for row_idx, row in enumerate(reader, start=1):
            try:
                # -----------------------------------------------------------
                # 1. Determine Context (Country & Regulation)
                # -----------------------------------------------------------
                target_country = country
                target_regulations = regulations

                if not target_country:
                    # Global Mode: Lookup Country
                    c_code = clean(row.get('country_code')).upper()
                    if not c_code:
                        raise ValueError(f"Row {row_idx}: Missing 'country_code' for global upload.")
                    try:
                        target_country = Country.objects.get(iso2_code=c_code)
                    except Country.DoesNotExist:
                        raise ValueError(f"Row {row_idx}: Country code '{c_code}' not found.")

                if not target_regulations:
                    # Global Mode: Lookup Regulation by Fiscal Year
                    f_year = parse_int(row.get('fiscal_year'))
                    if not f_year:
                        raise ValueError(f"Row {row_idx}: Missing 'fiscal_year' for global upload.")
                    
                    # Assuming one regulation per fiscal year per country
                    # Adjust filtering if you have multiple active regulations per year
                    target_regulations = Regulations.objects.filter(
                        country=target_country, 
                        fiscal_year=f_year
                    ).first()

                    if not target_regulations:
                        raise ValueError(f"Row {row_idx}: No Regulations found for {target_country.iso2_code} in year {f_year}.")

                # -----------------------------------------------------------
                # 2. Lookup Elements
                # -----------------------------------------------------------
                e_code = clean(row.get('element_code'))
                if not e_code:
                    raise ValueError(f"Row {row_idx}: Missing 'element_code'.")
                
                try:
                    element_obj = Element.objects.get(country=target_country, element_code=e_code)
                except Element.DoesNotExist:
                    raise ValueError(f"Row {row_idx}: Element code '{e_code}' not found in {target_country.name}.")

                # Optional Base Element
                base_code = clean(row.get('element_base_code'))
                element_base_obj = None
                if base_code:
                    try:
                        element_base_obj = Element.objects.get(country=target_country, element_code=base_code)
                    except Element.DoesNotExist:
                        raise ValueError(f"Row {row_idx}: Base Element code '{base_code}' not found.")

                # -----------------------------------------------------------
                # 3. Prepare Data Dictionary
                # -----------------------------------------------------------
                data = {
                    'base_frequency': clean(row.get('base_frequency', 'Monthly')),
                    'rounding_base': clean(row.get('rounding_base', 'None')),
                    'rounding_base_decimals': parse_int(row.get('rounding_base_decimals'), 2),
                    'rounding_taxed': clean(row.get('rounding_taxed', 'None')),
                    'rounding_taxed_decimals': parse_int(row.get('rounding_taxed_decimals'), 2),
                    'element_base': element_base_obj,
                }

                # Loop through Brackets 00-15
                for i in range(16):
                    suffix = f"{i:02d}"
                    data[f'bracket_{suffix}'] = parse_dec(row.get(f'bracket_{suffix}'))
                    data[f'rate_{suffix}'] = parse_dec(row.get(f'rate_{suffix}'))
                    data[f'round_bracket_logic_{suffix}'] = clean(row.get(f'round_bracket_logic_{suffix}', 'None'))
                    data[f'round_bracket_dec_{suffix}'] = parse_int(row.get(f'round_bracket_dec_{suffix}'), 2)
                    data[f'round_result_logic_{suffix}'] = clean(row.get(f'round_result_logic_{suffix}', 'None'))
                    data[f'round_result_dec_{suffix}'] = parse_int(row.get(f'round_result_dec_{suffix}'), 2)

                # -----------------------------------------------------------
                # 4. Update or Create
                # -----------------------------------------------------------
                obj, created = CalculationBase.objects.update_or_create(
                    country=target_country,
                    regulations=target_regulations,
                    element=element_obj,
                    defaults=data
                )
                success_count += 1

            except Exception as e:
                error_count += 1
                errors.append(str(e))

        if dry_run:
            transaction.savepoint_rollback(sid)

    return success_count, error_count, errors