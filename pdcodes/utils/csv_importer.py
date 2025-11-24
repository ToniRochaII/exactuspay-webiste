import csv
from io import TextIOWrapper


def clean_value(value):
    """Safely convert CSV cell values without executing code."""
    if value is None:
        return None

    value = str(value).strip()

    # Empty value → None
    if value == "":
        return None

    # Boolean conversion
    lowered = value.lower()
    if lowered in ["true", "yes", "1"]:
        return True
    if lowered in ["false", "no", "0"]:
        return False

    # Integer conversion
    if value.isdigit():
        return int(value)

    # Float conversion
    try:
        float_val = float(value)
        return float_val
    except ValueError:
        pass

    # Leave all other values as strings
    return value


def import_pdcodes_from_csv(
    file,
    company,
    field_map: dict,
    required_fields: list = None,
    dry_run: bool = False,
    update_existing: bool = True,
):
    """
    Generic CSV importer for PD Codes.
    - Performs safe value conversion (no eval)
    - Validates required fields
    - Creates or updates objects
    - Supports dry run mode
    """

    required_fields = required_fields or []
    result = {
        "created": 0,
        "updated": 0,
        "errors": [],
        "rows": [],
    }

    # Read CSV safely
    decoded = TextIOWrapper(file, encoding="utf-8")
    reader = csv.DictReader(decoded)

    from pdcodes.models import PDcode  # safe import inside function

    for row_number, row in enumerate(reader, start=2):  # header = row 1
        row_errors = []

        # Build PDcode data dict
        data = {}

        for csv_field, model_field in field_map.items():

            raw_value = row.get(csv_field, "").strip()

            cleaned = clean_value(raw_value)
            data[model_field] = cleaned

        # Validate required fields
        for req in required_fields:
            if not data.get(req):
                row_errors.append(f"Missing required field: {req}")

        if row_errors:
            result["errors"].append(
                f"Row {row_number}: " + "; ".join(row_errors)
            )
            continue

        # Check if PDcode exists
        existing = PDcode.objects.filter(
            company=company,
            pdcode_code=data.get("pdcode_code")
        ).first()

        if existing:
            if update_existing:
                # Update existing
                for k, v in data.items():
                    setattr(existing, k, v)
                if not dry_run:
                    try:
                        existing.save()
                    except Exception as e:
                        result["errors"].append(
                            f"Row {row_number}: failed to update — {str(e)}"
                        )
                        continue
                result["updated"] += 1
            else:
                result["rows"].append(
                    f"Row {row_number}: skipped (already exists)"
                )
            continue

        # Create new PDcode
        new_obj = PDcode(company=company, **data)

        if not dry_run:
            try:
                new_obj.save()
            except Exception as e:
                result["errors"].append(
                    f"Row {row_number}: failed to create — {str(e)}"
                )
                continue

        result["created"] += 1

    return result


# pdcodes/utils/csv_importer.py - Add this function
def import_pdcodes_to_all_companies(file, companies, field_map, required_fields=None, dry_run=False, update_existing=True):
    """
    Import PD codes to all specified companies from a single CSV file
    """
    all_results = {}
    
    try:
        # Read file once
        file_obj = TextIOWrapper(file, encoding='utf-8-sig')
        reader = csv.DictReader(file_obj)
        rows = list(reader)
        
        if not rows:
            return {"error": "CSV file is empty"}
        
        # Validate required fields
        missing_fields = [f for f in required_fields or [] if f not in reader.fieldnames]
        if missing_fields:
            return {"error": f"Missing required fields: {', '.join(missing_fields)}"}
        
        # Process for each company
        for company in companies:
            company_results = import_pdcodes_from_csv(
                file=file,  # Note: we need to reset file pointer or use rows
                company=company,
                field_map=field_map,
                required_fields=required_fields,
                dry_run=dry_run,
                update_existing=update_existing
            )
            all_results[company.company_code] = {
                **company_results,
                "company_name": company.trade_name,
                "company_id": company.company_id
            }
            
    except Exception as e:
        return {"error": f"Country-wide upload error: {str(e)}"}
    
    return all_results

# Alternative implementation that processes rows directly
def import_pdcodes_to_all_companies_direct(file, companies, field_map, required_fields=None, dry_run=False, update_existing=True):
    """
    More efficient implementation that processes rows directly for all companies
    """
    all_results = {}
    
    try:
        # Read file
        file_obj = TextIOWrapper(file, encoding='utf-8-sig')
        reader = csv.DictReader(file_obj)
        rows = list(reader)
        
        if not rows:
            return {"error": "CSV file is empty"}
        
        # Validate required fields
        missing_fields = [f for f in required_fields or [] if f not in reader.fieldnames]
        if missing_fields:
            return {"error": f"Missing required fields: {', '.join(missing_fields)}"}
        
        # Initialize results for each company
        for company in companies:
            all_results[company.company_code] = {
                "created": 0,
                "updated": 0,
                "errors": [],
                "company_name": company.trade_name,
                "company_id": company.company_id,
                "dry_run": dry_run
            }
        
        @transaction.atomic
        def run_import():
            for i, row in enumerate(rows, start=1):
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                # Process row for each company
                for company in companies:
                    result_key = company.company_code
                    
                    try:
                        # Prepare data for PDcode
                        data = {}
                        for csv_col, model_field in field_map.items():
                            if csv_col in row and row[csv_col] not in [None, ""]:
                                # Handle boolean fields
                                if model_field.startswith('pdcode_') and hasattr(PDcode, model_field):
                                    field = PDcode._meta.get_field(model_field)
                                    if isinstance(field, models.BooleanField):
                                        data[model_field] = str(row[csv_col]).lower() in ('true', 'yes', '1', 'y')
                                    else:
                                        data[model_field] = row[csv_col]
                                else:
                                    data[model_field] = row[csv_col]
                        
                        # Get PD code for lookup
                        pdcode_code = data.get('pdcode_code')
                        if not pdcode_code:
                            all_results[result_key]['errors'].append(f"Row {i}: PD Code is required")
                            continue
                        
                        # Check if PD code already exists for this company
                        existing_pdcode = PDcode.objects.filter(
                            company=company, 
                            pdcode_code=pdcode_code
                        ).first()
                        
                        if existing_pdcode:
                            if update_existing:
                                # Update existing PD code
                                for field, value in data.items():
                                    if field != 'pdcode_code':  # Don't update the code itself
                                        setattr(existing_pdcode, field, value)
                                existing_pdcode.save()
                                all_results[result_key]['updated'] += 1
                            else:
                                all_results[result_key]['errors'].append(f"Row {i}: PD Code '{pdcode_code}' already exists")
                        else:
                            # Create new PD code
                            pdcode = PDcode(company=company, **data)
                            pdcode.full_clean()
                            pdcode.save()
                            all_results[result_key]['created'] += 1
                            
                    except Exception as e:
                        all_results[result_key]['errors'].append(f"Row {i}: {str(e)}")

            # Rollback if dry run
            if dry_run:
                transaction.set_rollback(True)
                # Reset counts for dry run
                for result in all_results.values():
                    result['created'] = 0
                    result['updated'] = 0

        run_import()

    except Exception as e:
        return {"error": f"Country-wide upload error: {str(e)}"}
    
    return all_results# pdcodes/utils/csv_importer.py - Add this function
def import_pdcodes_to_all_companies(file, companies, field_map, required_fields=None, dry_run=False, update_existing=True):
    """
    Import PD codes to all specified companies from a single CSV file
    """
    all_results = {}
    
    try:
        # Read file once
        file_obj = TextIOWrapper(file, encoding='utf-8-sig')
        reader = csv.DictReader(file_obj)
        rows = list(reader)
        
        if not rows:
            return {"error": "CSV file is empty"}
        
        # Validate required fields
        missing_fields = [f for f in required_fields or [] if f not in reader.fieldnames]
        if missing_fields:
            return {"error": f"Missing required fields: {', '.join(missing_fields)}"}
        
        # Process for each company
        for company in companies:
            company_results = import_pdcodes_from_csv(
                file=file,  # Note: we need to reset file pointer or use rows
                company=company,
                field_map=field_map,
                required_fields=required_fields,
                dry_run=dry_run,
                update_existing=update_existing
            )
            all_results[company.company_code] = {
                **company_results,
                "company_name": company.trade_name,
                "company_id": company.company_id
            }
            
    except Exception as e:
        return {"error": f"Country-wide upload error: {str(e)}"}
    
    return all_results

# Alternative implementation that processes rows directly
def import_pdcodes_to_all_companies_direct(file, companies, field_map, required_fields=None, dry_run=False, update_existing=True):
    """
    More efficient implementation that processes rows directly for all companies
    """
    all_results = {}
    
    try:
        # Read file
        file_obj = TextIOWrapper(file, encoding='utf-8-sig')
        reader = csv.DictReader(file_obj)
        rows = list(reader)
        
        if not rows:
            return {"error": "CSV file is empty"}
        
        # Validate required fields
        missing_fields = [f for f in required_fields or [] if f not in reader.fieldnames]
        if missing_fields:
            return {"error": f"Missing required fields: {', '.join(missing_fields)}"}
        
        # Initialize results for each company
        for company in companies:
            all_results[company.company_code] = {
                "created": 0,
                "updated": 0,
                "errors": [],
                "company_name": company.trade_name,
                "company_id": company.company_id,
                "dry_run": dry_run
            }
        
        @transaction.atomic
        def run_import():
            for i, row in enumerate(rows, start=1):
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                # Process row for each company
                for company in companies:
                    result_key = company.company_code
                    
                    try:
                        # Prepare data for PDcode
                        data = {}
                        for csv_col, model_field in field_map.items():
                            if csv_col in row and row[csv_col] not in [None, ""]:
                                # Handle boolean fields
                                if model_field.startswith('pdcode_') and hasattr(PDcode, model_field):
                                    field = PDcode._meta.get_field(model_field)
                                    if isinstance(field, models.BooleanField):
                                        data[model_field] = str(row[csv_col]).lower() in ('true', 'yes', '1', 'y')
                                    else:
                                        data[model_field] = row[csv_col]
                                else:
                                    data[model_field] = row[csv_col]
                        
                        # Get PD code for lookup
                        pdcode_code = data.get('pdcode_code')
                        if not pdcode_code:
                            all_results[result_key]['errors'].append(f"Row {i}: PD Code is required")
                            continue
                        
                        # Check if PD code already exists for this company
                        existing_pdcode = PDcode.objects.filter(
                            company=company, 
                            pdcode_code=pdcode_code
                        ).first()
                        
                        if existing_pdcode:
                            if update_existing:
                                # Update existing PD code
                                for field, value in data.items():
                                    if field != 'pdcode_code':  # Don't update the code itself
                                        setattr(existing_pdcode, field, value)
                                existing_pdcode.save()
                                all_results[result_key]['updated'] += 1
                            else:
                                all_results[result_key]['errors'].append(f"Row {i}: PD Code '{pdcode_code}' already exists")
                        else:
                            # Create new PD code
                            pdcode = PDcode(company=company, **data)
                            pdcode.full_clean()
                            pdcode.save()
                            all_results[result_key]['created'] += 1
                            
                    except Exception as e:
                        all_results[result_key]['errors'].append(f"Row {i}: {str(e)}")

            # Rollback if dry run
            if dry_run:
                transaction.set_rollback(True)
                # Reset counts for dry run
                for result in all_results.values():
                    result['created'] = 0
                    result['updated'] = 0

        run_import()

    except Exception as e:
        return {"error": f"Country-wide upload error: {str(e)}"}
    
    return all_results