from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR
from .uk_tax_logic import UKTaxLogic

class UnitedKingdomPayrollStrategy:
    def __init__(self, payroll_calculator):
        self.calc = payroll_calculator
        self.employee = payroll_calculator.employee

    def process_nuances(self):
        """
        Implements UK Tax Logic.
        1. Calculates Allowance.
        2. Identifies Flat Rate Codes (BR, D0, D1) and applies explicit calculation.
        """
        # 1. FETCH DATA
        raw_code = getattr(self.employee, 'tax_info_03', '1257L') or '1257L'
        raw_basis = getattr(self.employee, 'tax_info_04', 'Cumulative') or 'Cumulative'
        
        # 2. INITIALIZE PARSER
        tax_logic = UKTaxLogic(raw_code, explicit_basis=raw_basis)
        freq = self.calc.period.frequency if self.calc.period else "monthly"
        period_num = self.calc.period.period_number if self.calc.period else 1

        # 3. REGISTER ALLOWANCE
        adjustment_amount = tax_logic.get_period_allowance(freq, period=period_num)
        desc = f"Tax Code {tax_logic.raw_code}"
        if "K" in tax_logic.prefix: desc += " (Additional Pay)"
        else: desc += " (Tax Free Allowance)"

        self.calc.results_dict['5500'] = adjustment_amount
        self.calc.register("Tax Adjustment", adjustment_amount, "5500", description=desc)

        # 4. PREPARE TAXABLE BASE (Code 86000)
        gross_source = self.calc.results_dict.get('85000', Decimal('0.00'))
        adjusted_base = tax_logic.calculate_taxable_pay(gross_source, freq, period_num)
        self.calc.results_dict['86000'] = adjusted_base 
        
        # 5. FLAT RATE CODES (Explicit Calculation)
        flat_rates = {
            "BR": Decimal("0.20"),
            "D0": Decimal("0.40"),
            "D1": Decimal("0.45")
        }
        
        current_code = tax_logic.clean_code
        
        if current_code in flat_rates:
            rate = flat_rates[current_code]
            
            # Formula: Round Taxable Pay DOWN to whole pounds, then multiply by rate.
            # Example: 8439.95 -> 8439.00 -> * 40%
            taxable_rounded = adjusted_base.quantize(Decimal("1."), rounding=ROUND_FLOOR)
            tax_amount = taxable_rounded * rate
            
            # Final result is standard 2 decimal rounding
            tax_amount = tax_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            
            # Register Tax (Negative for deduction)
            self.calc.results_dict['6000'] = -tax_amount
            self.calc.register("PAYE Income Tax", -tax_amount, "6000")
            
            # --- CRITICAL FIX: THE LOCK ---
            # This prevents the Database Engine from calculating tax again!
            if not hasattr(self.calc, 'explicit_overrides'):
                self.calc.explicit_overrides = set()
            self.calc.explicit_overrides.add('6000')
            # ------------------------------