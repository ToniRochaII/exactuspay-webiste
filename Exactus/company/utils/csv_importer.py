import csv
from django.db import transaction
from django.core.exceptions import ValidationError
from Exactus.country.models import Country
from Exactus.company.models import Company

def import_companies_from_csv(io_string, country=None, dry_run=False):
    """
    Imports companies from a CSV file.

    Args:
        io_string (io.StringIO): The CSV content stream.
        country (Country, optional): If provided, all rows are imported into this country.
                                     If None, the 'country_code' column is required per row.
        dry_run (bool): If True, performs all validations but rolls back changes at the end.

    Returns:
        tuple: (success_count, error_count, errors_list)
    """
    reader = csv.DictReader(io_string)
    success_count = 0
    error_count = 0
    errors = []

    # Helper to clean strings
    def clean_str(val):
        if val is None:
            return ""
        return str(val).strip()

    with transaction.atomic():
        if dry_run:
            sid = transaction.savepoint()

        for row_idx, row in enumerate(reader, start=1):
            try:
                # -----------------------------------------------------------
                # 1. Determine Target Country
                # -----------------------------------------------------------
                target_country = country
                
                # Global Mode: Look up country from CSV
                if not target_country:
                    iso_code = clean_str(row.get('country_code')).upper()
                    if not iso_code:
                        raise ValueError(f"Row {row_idx}: Missing 'country_code' (Global Mode).")
                    
                    try:
                        target_country = Country.objects.get(iso2_code=iso_code)
                    except Country.DoesNotExist:
                        raise ValueError(f"Row {row_idx}: Country code '{iso_code}' not found.")

                # -----------------------------------------------------------
                # 2. Validate Required Fields
                # -----------------------------------------------------------
                company_code = clean_str(row.get('company_code'))
                trade_name = clean_str(row.get('trade_name'))

                if not company_code:
                    raise ValueError(f"Row {row_idx}: Missing required field 'company_code'.")
                
                if not trade_name:
                    raise ValueError(f"Row {row_idx}: Missing required field 'trade_name'.")

                # -----------------------------------------------------------
                # 3. Prepare Data
                # -----------------------------------------------------------
                company_data = {
                    'company_number': clean_str(row.get('company_number')),
                    'trade_name': trade_name,
                    'legal_name': clean_str(row.get('legal_name')),
                    
                    # Address
                    'building_name': clean_str(row.get('building_name')),
                    'road_name_1': clean_str(row.get('road_name_1')),
                    'road_name_2': clean_str(row.get('road_name_2')),
                    'town': clean_str(row.get('town')),
                    'post_code': clean_str(row.get('post_code')),
                    
                    # IDs
                    'tax_id_01': clean_str(row.get('tax_id_01')),
                    'tax_id_02': clean_str(row.get('tax_id_02')),
                    'tax_id_03': clean_str(row.get('tax_id_03')),
                    'tax_id_04': clean_str(row.get('tax_id_04')),
                    'tax_id_05': clean_str(row.get('tax_id_05')),
                    
                    # Credentials
                    'rti_user_id': clean_str(row.get('rti_user_id')),
                    'rti_password': clean_str(row.get('rti_password')),
                    
                    # Status
                    'account_status': clean_str(row.get('account_status', 'ACTIVE')).upper()
                }

                # -----------------------------------------------------------
                # 4. Update or Create
                # -----------------------------------------------------------
                # Uniqueness is defined by (Country + Company Code)
                obj, created = Company.objects.update_or_create(
                    country=target_country,
                    company_code=company_code,
                    defaults=company_data
                )

                success_count += 1

            except Exception as e:
                error_count += 1
                errors.append(str(e))

        if dry_run:
            transaction.savepoint_rollback(sid)

    return success_count, error_count, errors