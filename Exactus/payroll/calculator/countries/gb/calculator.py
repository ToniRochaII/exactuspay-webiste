from decimal import Decimal
from .uk_tax_logic import UKTaxCodeParser

class UnitedKingdomPayrollStrategy:
    def __init__(self, payroll_calculator):
        self.calc = payroll_calculator
        self.employee = payroll_calculator.employee

    def process_nuances(self):
        """
        Implements UK Tax Logic with explicit Element 10000 (Tax Free Allowance).
        Flow:
        1. Calculate Tax Free Allowance.
        2. Store as Element 10000.
        3. 86000 (Tax Base) = 85000 (Gross) - 10000 (Allowance).
        """
        # 1. FETCH DATA
        raw_code = getattr(self.employee, 'tax_info_03', '1257L') or '1257L'
        raw_basis = getattr(self.employee, 'tax_info_04', 'Cumulative') or 'Cumulative'
        
        # 2. PARSE TAX CODE & GET ALLOWANCE
        parser = UKTaxCodeParser(raw_code, explicit_basis=raw_basis)
        freq = self.calc.period.frequency if self.calc.period else "monthly"
        allowance = parser.get_period_allowance(freq)
        
        # 3. CREATE ELEMENT 10000 (Tax Free Allowance)
        # We explicitly store the allowance as a payroll element.
        # This ensures it appears on the payslip and in reports.
        self.calc.results_dict['10000'] = allowance
        
        # Register for Payslip UI (Standardized Element)
        self.calc.register(
            name="Tax Free Allowance",
            amount=allowance,
            code="10000",
            description=f"Tax Code {parser.raw_code}"
        )

        # 4. GET SOURCE (Code 85000 - Gross Taxable Pay)
        gross_taxable_source = self.calc.results_dict.get('85000', Decimal('0.00'))

        # 5. CALCULATE TARGET (Code 86000 - Net Taxable Pay)
        # Logic: Gross (85000) - Allowance (10000) = Tax Base (86000)
        adjusted_base = gross_taxable_source - allowance
        
        # Safety check: Tax base cannot be negative
        if adjusted_base < 0:
            adjusted_base = Decimal("0.00")

        # 6. OVERWRITE 86000
        # The Tax Engine will now use this adjusted base to calculate Code 6000.
        self.calc.results_dict['86000'] = adjusted_base
        
        # Optional: Store metadata for audit
        self.calc.results_dict['TAX_CODE'] = parser.raw_code