# elements/utils/csv_importer.py
import csv
from django.contrib import messages
from country.models import Country
from elements.models import Element

def import_elements_from_csv(csv_file, country=None):
    """
    Import elements from CSV file
    Returns: (success_count, error_count, errors_list)
    """
    reader = csv.DictReader(csv_file)
    success_count = 0
    error_count = 0
    errors = []
    
    for row_num, row in enumerate(reader, start=2):  # start=2 to account for header
        try:
            # Get country from row or use provided country
            country_code = row.get('country_code', '')
            if country:
                element_country = country
            elif country_code:
                element_country = Country.objects.filter(code=country_code).first()
                if not element_country:
                    error_count += 1
                    errors.append(f"Row {row_num}: Country with code '{country_code}' not found")
                    continue
            else:
                error_count += 1
                errors.append(f"Row {row_num}: No country specified")
                continue
            
            # Check if element already exists
            element_code = row.get('element_code', '')
            existing_element = Element.objects.filter(
                country=element_country, 
                element_code=element_code
            ).first()
            
            if existing_element:
                # Update existing element
                for field, value in row.items():
                    if hasattr(existing_element, field) and field != 'country_code':
                        setattr(existing_element, field, value)
                existing_element.save()
            else:
                # Create new element
                element_data = {
                    'country': element_country,
                    'element_code': element_code,
                    'element_name': row.get('element_name', ''),
                    'element_description': row.get('element_description', ''),
                    'element_status': row.get('element_status', 'Visible'),
                    'element_account': row.get('element_account', ''),
                    'element_map_code': row.get('element_map_code', ''),
                    'element_gl_account': row.get('element_gl_account', ''),
                    'element_frequency': row.get('element_frequency', 'Recurring'),
                    'element_type': row.get('element_type', 'Regular'),
                    'element_class': row.get('element_class', 'statutory'),
                    'element_category': row.get('element_category', 'Deduction'),
                    'element_taxable': row.get('element_taxable', 'FALSE').upper() == 'TRUE',
                    'element_tax_flat': row.get('element_tax_flat', 'FALSE').upper() == 'TRUE',
                    'element_tax_irregular': row.get('element_tax_irregular', 'FALSE').upper() == 'TRUE',
                    'element_social_securitable': row.get('element_social_securitable', 'FALSE').upper() == 'TRUE',
                    'element_pensionable': row.get('element_pensionable', 'FALSE').upper() == 'TRUE',
                    'element_payable': row.get('element_payable', 'TRUE').upper() == 'TRUE',
                    'element_calculate': row.get('element_calculate', 'TRUE').upper() == 'TRUE',
                    'element_categorytype': row.get('element_categorytype', 'Bracketable'),
                    'archive': row.get('archive', 'N')
                }
                Element.objects.create(**element_data)
            
            success_count += 1
            
        except Exception as e:
            error_count += 1
            errors.append(f"Row {row_num}: {str(e)}")
            continue
    
    return success_count, error_count, errors