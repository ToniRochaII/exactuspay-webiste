from decimal import Decimal
from Exactus.payroll.calculator.countries.base import CountryPayrollStrategy 

class BrazilPayrollStrategy(CountryPayrollStrategy):
    def process_nuances(self):
        """
        Brazil Logic Implementation:
        - Uses Taxable Income (Code 86000) as the threshold trigger.
        - Threshold: 7350.00
        - > 7350.00: Applies High Earner Tax (Code 6001), removes 6000.
        - <= 7350.00: Applies Standard Tax (Code 6000), removes 6001.
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
        Rule: Use Code 6000 (Standard). Remove 6001.
        """
        # Example 7.5% Tax (Replace with your actual table/rate logic)
        tax = base_val * Decimal('0.00')
        
        # A. Register correct code
        self.calc.register("Income Tax (Standard)", -tax, "6000")
        
        # B. FORCE REMOVE conflicting code (6001)
        # We try removing both string and int keys to be safe
        self.results.pop('6001', None)
        self.results.pop(6001, None)

    def _apply_high_earner_tax(self, base_val):
        """
        Applied when Taxable Income > 7350.
        Rule: Use Code 6001 (High Earner). Remove 6000.
        """
        # Example High Earner Calculation (Fixed ceiling or different rate)
        # Note: Adjust this formula to match your exact high earner tax rule
        tax = Decimal('0.00') 
        
        # A. Register correct code
        self.calc.register("Income Tax (High Earner)", -tax, "6001")
        
        # B. FORCE REMOVE conflicting code (6000)
        # This fixes the "Double Taxation" issue seen in your database
        self.results.pop('6000', None)
        self.results.pop(6000, None)