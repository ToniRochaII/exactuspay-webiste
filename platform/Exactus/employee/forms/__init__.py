from .base_employee_form import BaseEmployeeForm, EmployeeUploadForm
from .brazil_employee_form import BrazilEmployeeForm
from .united_kingdom_employee_form import UnitedKingdomEmployeeForm
from .argentina_employee_form import ArgentinaEmployeeForm
from .access_form import EmployeeAccessForm  # <--- NEW IMPORT
from .utils import get_employee_form_for_country, get_country_specific_fields
from .compensation import CompensationForm

# Create alias for backward compatibility
EmployeeForm = BaseEmployeeForm

__all__ = [
    'BaseEmployeeForm',
    'EmployeeForm',
    'EmployeeUploadForm',
    'EmployeeAccessForm',
    'BrazilEmployeeForm',
    'UnitedKingdomEmployeeForm',
    'ArgentinaEmployeeForm',
    'get_employee_form_for_country',
    'get_country_specific_fields',
]