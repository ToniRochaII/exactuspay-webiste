import csv
from django.db import transaction
from Exactus.country.models import Country
from Exactus.elements.models import Element

def import_elements_from_csv(io_string, country=None, dry_run=False):
    """
    Imports Elements from CSV.
    - Global Mode: Looks up 'country_code' from CSV.
    - Local Mode: Uses the 'country' argument passed to the function.
    """
    reader = csv.DictReader(io_string)
    success_count = 0
    error_count = 0
    errors = []

    # List of boolean fields to convert from strings "TRUE"/"FALSE"
    bool_fields = [
        'element_taxable', 'element_tax_flat', 'element_tax_irregular',
        'element_social_securitable', 'element_pensionable', 
        'element_payable', 'element_calculate'
    ]

    with transaction.atomic():
        if dry_run:
            sid = transaction.savepoint()

        for row_idx, row in enumerate(reader, start=1):
            try:
                # -----------------------------------------------------------
                # 1. Determine Target Country
                # -----------------------------------------------------------
                target_country = country
                if not target_country:
                    c_code = row.get('country_code', '').strip().upper()
                    if not c_code:
                        raise ValueError(f"Row {row_idx}: Missing 'country_code' for global upload.")
                    
                    try:
                        target_country = Country.objects.get(iso2_code=c_code)
                    except Country.DoesNotExist:
                        raise ValueError(f"Row {row_idx}: Country code '{c_code}' not found.")

                # -----------------------------------------------------------
                # 2. Validate Key Data
                # -----------------------------------------------------------
                element_code = row.get('element_code', '').strip()
                if not element_code:
                    raise ValueError(f"Row {row_idx}: Missing 'element_code'.")

                # -----------------------------------------------------------
                # 3. Prepare Data
                # -----------------------------------------------------------
                defaults = {
                    'element_name': row.get('element_name', '').strip(),
                    'element_description': row.get('element_description', '').strip(),
                    'element_status': row.get('element_status', 'Visible').strip(),
                    'element_account': row.get('element_account', '').strip(),
                    'element_map_code': row.get('element_map_code', '').strip(),
                    'element_gl_account': row.get('element_gl_account', '').strip(),
                    'element_frequency': row.get('element_frequency', 'Recurring').strip(),
                    'element_type': row.get('element_type', 'Regular').strip(),
                    'element_class': row.get('element_class', 'Standard').strip(),
                    'element_category': row.get('element_category', 'Payment').strip(),
                    'element_categorytype': row.get('element_categorytype', 'Base').strip(),
                    'archive': row.get('archive', 'N').strip().upper()[:1] or 'N',
                }

                # Handle Boolean Conversions
                for field in bool_fields:
                    val = row.get(field, 'FALSE').strip().upper()
                    # Accept TRUE, 1, YES, T as True
                    defaults[field] = (val in ['TRUE', '1', 'YES', 'T'])

                # -----------------------------------------------------------
                # 4. Update or Create
                # -----------------------------------------------------------
                # Unique identifier is (Country + Element Code)
                obj, created = Element.objects.update_or_create(
                    country=target_country,
                    element_code=element_code,
                    defaults=defaults
                )
                success_count += 1

            except Exception as e:
                error_count += 1
                errors.append(str(e))

        if dry_run:
            transaction.savepoint_rollback(sid)

    return success_count, error_count, errors