import unittest
import sys
import os
from decimal import Decimal
from unittest.mock import MagicMock
import logging

# --- MOCK SETUP ---
sys.modules["django"] = MagicMock()
sys.modules["django.db"] = MagicMock()
sys.modules["django.db.models"] = MagicMock()
sys.modules["django.conf"] = MagicMock()
sys.modules["django.db.models.Q"] = MagicMock()

mock_modules = [
    "Exactus.elements.models",
    "Exactus.calculationbase.models",
    "Exactus.country.models",
    "Exactus.company.models",
    "Exactus.employee.models",
    "Exactus.payroll.models",
]
for mod in mock_modules:
    sys.modules[mod] = MagicMock()

sys.path.append(os.getcwd())

try:
    from Exactus.payroll.calculator.universal import UniversalPayrollCalculator
except ImportError:
    print("CRITICAL: Cannot import Calculator. Check path.")
    sys.exit(1)

logging.disable(logging.CRITICAL)

# --- MOCK HELPERS ---
class MockQuerySet(list):
    def filter(self, *args, **kwargs): return self
    def select_related(self, *args, **kwargs): return self
    def all(self): return self

class MockBaseLink:
    """Simulates a link to a base (e.g., linking Pension to 85000)"""
    def __init__(self, code):
        self.element_code = code

class MockPDCode:
    def __init__(self, code, description, payable=True, taxable=True, category="EARNING", linked_bases=None):
        self.pdcode_code = code
        self.pdcode_description = description
        self.pdcode_payable = payable
        self.pdcode_taxable = taxable
        self.pdcode_social_securitable = True
        self.category = category
        
        # Category Logic
        if category == "DEDUCTION":
            self.pdcode_category = "DEDUCTION"
        else:
            self.pdcode_category = "EARNING"
            
        # Explicit Base Linking Logic
        # This simulates the 'applicable_bases' ManyToMany relationship
        self.applicable_bases = MagicMock()
        if linked_bases:
            # Create a list of MockBaseLink objects
            base_objs = [MockBaseLink(b_code) for b_code in linked_bases]
            self.applicable_bases.all.return_value = base_objs
        else:
            self.applicable_bases.all.return_value = []

class MockComp:
    def __init__(self, amount, pdcode):
        self.amount = Decimal(str(amount))
        self.pdcode = pdcode
        self.start_date = "2024-01-01"
        self.end_date = None
        self.is_active = True
        self.processed = False
        self.category = pdcode.category
        self.frequency = "monthly"

    def get_period_amount(self, start, end):
        return self.amount

class TestUKPayrollScenario(unittest.TestCase):
    
    def setUp(self):
        self.employee = MagicMock()
        self.employee.employee_name = "Employee"
        
        # Tax Data
        self.employee.tax_info_03 = "1257L" 
        self.employee.tax_info_04 = "Cumulative"
        self.employee.tax_info_05 = "A"
        
        self.period = MagicMock()
        self.period.start_date = "2024-04-01"
        self.period.end_date = "2024-04-30"
        self.period.frequency = "monthly"
        self.period.payroll.country.slug = "gb" 

        # --- SETUP INPUTS ---
        # 1. Basic Pay (3500)
        self.pd_1000 = MockPDCode("1000", "Basic Pay")
        
        # 2. Bonus (3500)
        self.pd_1200 = MockPDCode("1200", "Bonus")
        
        # 3. Pension (155) - CRITICAL CHANGE HERE
        # We explicitly link this deduction to Base '85000' so the calculator knows 
        # to subtract it from the Gross Taxable Pay.
        self.pd_2200 = MockPDCode("2200", "Pension", category="DEDUCTION", linked_bases=['85000'])

        self.comps_list = [
            MockComp(3500.00, self.pd_1000),
            MockComp(3500.00, self.pd_1200),
            MockComp(155.00, self.pd_2200)
        ]
        self.queryset = MockQuerySet(self.comps_list)
        self.employee.compensationcomponent_set = self.queryset

    def test_uk_image_scenario(self):
        calc = UniversalPayrollCalculator(self.employee, self.period)
        result = calc.calculate()
        data = result['elements']

        print("\n--- TEST: UK IMAGE SCENARIO ---")

        # 1. CHECK GROSS TAXABLE (Code 85000)
        # Expected: 3500 + 3500 - 155 = 6,845.00
        val_85000 = data.get('85000', Decimal('0.00'))
        expected_85000 = Decimal("6845.00")
        print(f"Code 85000: Expected {expected_85000} | Actual {val_85000}")
        self.assertEqual(val_85000, expected_85000, "Code 85000 mismatch")

        # 2. CHECK ALLOWANCE
        # 1257L -> 1047.50
        allowance = data.get('PERIOD_ALLOWANCE', Decimal('0.00'))
        expected_allowance = Decimal("1047.50")
        print(f"Allowance : Expected {expected_allowance} | Actual {allowance}")
        self.assertEqual(allowance, expected_allowance, "Allowance mismatch")

        # 3. CHECK CALCULATION BASE (Code 86000)
        # Expected: 6845.00 - 1047.50 = 5,797.50
        val_86000 = data.get('86000', Decimal('0.00'))
        expected_86000 = Decimal("5797.50")
        print(f"Code 86000: Expected {expected_86000} | Actual {val_86000}")
        self.assertEqual(val_86000, expected_86000, "Code 86000 mismatch")

        print("[SUCCESS] All figures match.")

if __name__ == '__main__':
    unittest.main()