from decimal import Decimal
from Exactus.payroll.calculator.countries.base import CountryPayrollStrategy 

class BrazilPayrollStrategy(CountryPayrollStrategy):
    def process_nuances(self):
        """
        Brazil Logic Implementation:
        - Uses Taxable Income (Code 86000) as the threshold trigger.
        - Threshold: 7350.00
        - > 7350.00: Applies High Earner Tax (Code 6001).
        - <= 7350.00: Applies Standard Tax (Code 6002).
        
        NOTE: We use Code 6002 for standard tax because Code 6000 is a 
        reporting total in the Universal Calculator and would be ignored 
        or overwritten if used directly.
        """
        # 1. Get Taxable Income (Accumulated in Universal Calculator as 86000)
        taxable_income = self.results.get('86000', Decimal('0.00'))
        
        # 2. Define Threshold
        THRESHOLD = Decimal('7350.00')
        
        # 3. Apply Mutually Exclusive Logic
        if taxable_income > THRESHOLD:
            self._apply_high_earner_tax(taxable_income)
        else:
            self._apply_standard_tax(taxable_income)

    def _apply_standard_tax(self, base_val):
        """
        Applied when Taxable Income <= 7350.
        Rule: Use Code 6002 (Standard). Remove 6001.
        """
        # --- INSERT REAL RATE HERE ---
        # Example: 7.5% Tax
        tax_rate = Decimal('0.00') # Update this with actual rate (e.g. 0.075)
        tax = base_val * tax_rate
        
        # A. Register correct code (6002 falls in valid 6xxx deduction range)
        self.calc.register("Income Tax (Standard)", -tax, "6002")
        
        # B. Remove conflicting High Earner code
        self.results.pop('6001', None)
        self.results.pop(6001, None)
        
        # C. LOCK: Prevent generic engine from overwriting tax
        # We tell the calculator "Don't try to calculate 6001 or 6000 later"
        self.calc.explicit_overrides.add('6001')
        self.calc.explicit_overrides.add('6000')

    def _apply_high_earner_tax(self, base_val):
        """
        Applied when Taxable Income > 7350.
        Rule: Use Code 6001 (High Earner). Remove 6002.
        """
        # --- INSERT REAL CALCULATION HERE ---
        # Example: Fixed ceiling or higher rate
        tax = Decimal('0.00') 
        
        # A. Register correct code (6001 falls in valid 6xxx deduction range)
        self.calc.register("Income Tax (High Earner)", -tax, "6001")
        
        # B. Remove conflicting Standard code (6002)
        self.results.pop('6002', None)
        self.results.pop(6002, None)
        
        # C. LOCK: Prevent generic engine from overwriting tax
        self.calc.explicit_overrides.add('6001')
        self.calc.explicit_overrides.add('6000')