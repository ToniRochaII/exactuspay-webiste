from decimal import Decimal
from Exactus.payroll.calculator.strategies import BasePayrollStrategy
# Import your logic class
from .tax_logic import UKTaxLogic 

class GBPayrollStrategy(BasePayrollStrategy):
    """
    GB-Specific Logic.
    Intervenes in the main calculation to apply Tax Codes (1257L, etc.)
    to the Taxable Pay Basis (86000).
    """

    def process_nuances(self):
        # 1. Fetch current Taxable Gross (Accumulated from 'taxable' pay elements)
        #    Default to 0.00 if no taxable elements were processed.
        raw_taxable_gross = self.calculator.results_dict.get('86000', Decimal('0.00'))

        # If 86000 is empty but we have a Total Gross (5000), 
        # we might assume Total Gross is Taxable (Fallback logic).
        # You can remove this 'if' block if you want strict separation.
        if raw_taxable_gross == 0 and self.calculator.results_dict.get('5000'):
             raw_taxable_gross = self.calculator.results_dict.get('5000')

        # 2. Get Employee Tax Details
        #    Adjust these field names to match your exact Employee model
        tax_code = getattr(self.calculator.employee, 'tax_info_03', '1257L') 
        basis = getattr(self.calculator.employee, 'tax_info_04', 'Cumulative')

        # 3. Initialize the Logic
        logic = UKTaxLogic(tax_code, explicit_basis=basis)

        # 4. Calculate the Adjusted Taxable Pay (Gross - Allowance)
        #    We pass the period number from the calculator context
        period_num = self.calculator.period.period_number
        
        # [CRITICAL STEP] 
        # This reduces the raw gross by the tax-free allowance
        adjusted_taxable_pay = logic.calculate_taxable_pay(
            raw_taxable_gross, 
            frequency=self.calculator.period.frequency, 
            period=period_num
        )

        # 5. UPDATE CODE 86000
        #    We overwrite 86000 so that when the TaxEngine runs next, 
        #    it calculates tax on this reduced amount.
        self.calculator.results_dict['86000'] = adjusted_taxable_pay
        
        # Optional: Store the original raw gross in a shadow code for reporting
        self.calculator.results_dict['86001'] = raw_taxable_gross