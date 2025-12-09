from .base_employee_form import BaseEmployeeForm, EmployeeUploadForm
from .brazil_employee_form import BrazilEmployeeForm
from .united_kingdom_employee_form import UnitedKingdomEmployeeForm
from .argentina_employee_form import ArgentinaEmployeeForm
from .utils import get_employee_form_for_country, get_country_specific_fields

# Create alias for backward compatibility
EmployeeForm = BaseEmployeeForm

__all__ = [
    'BaseEmployeeForm',
    'EmployeeForm',  # Keep this for backward compatibility
    'EmployeeUploadForm',
    'BrazilEmployeeForm',
    'UnitedKingdomEmployeeForm',
    'ArgentinaEmployeeForm',
    'get_employee_form_for_country',
    'get_country_specific_fields',
]