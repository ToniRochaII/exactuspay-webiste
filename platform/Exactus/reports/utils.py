import csv
import io
from django.http import HttpResponse
from django.conf import settings

# --- CHANGE STARTS HERE ---
try:
    from weasyprint import HTML, CSS
except (ImportError, OSError): # Now catches the missing library error
    HTML = None
    print("Warning: WeasyPrint system dependencies not found. PDF generation disabled.")
# --- CHANGE ENDS HERE ---

def render_to_pdf(html_string, base_url=None):
    if not HTML:
        raise RuntimeError("WeasyPrint unavailable (missing system dependencies: pango/cairo/gdk-pixbuf).")

    pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf()

    # Safety check: ensure bytes look like a PDF
    if not (pdf_bytes and pdf_bytes[:5] == b"%PDF-"):
        raise RuntimeError("PDF generation failed: output is not a valid PDF.")

    return pdf_bytes

# ... rest of the file remains the same ...
def render_to_csv(data_iterable, field_list=None):
    """
    Converts a QuerySet or list of objects into a CSV string.
    
    :param data_iterable: The list of objects (e.g. PayrollResult queryset)
    :param field_list: A list of strings matching the model attributes (e.g. ['employee.name', 'net_pay'])
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # 1. Determine Headers
    # If no specific fields are requested in settings, we try to guess or return empty
    if not field_list:
        # Fallback: Try to get all fields from the first object (if it's a model)
        if hasattr(data_iterable, 'model'):
            field_list = [field.name for field in data_iterable.model._meta.fields]
        elif data_iterable and hasattr(data_iterable[0], '__dict__'):
            field_list = list(data_iterable[0].__dict__.keys())
            # Remove internal Django state keys
            field_list = [f for f in field_list if not f.startswith('_')]
        else:
            return "" # Cannot generate CSV without fields

    # Write Header Row
    # specific logic to handle 'employee.first_name' type lookups
    headers = [f.replace('__', '.').replace('_', ' ').title() for f in field_list]
    writer.writerow(headers)

    # 2. Write Data Rows
    for obj in data_iterable:
        row = []
        for field in field_list:
            value = get_nested_attr(obj, field)
            row.append(str(value) if value is not None else "")
        writer.writerow(row)

    return output.getvalue()

def get_nested_attr(obj, attr_path):
    """
    Helper to retrieve 'employee.department.name' from an object.
    """
    try:
        for attr in attr_path.split('.'):
            # Handle dictionary access if the object is a dict
            if isinstance(obj, dict):
                obj = obj.get(attr)
            else:
                obj = getattr(obj, attr)
        return obj
    except (AttributeError, KeyError):
        return None