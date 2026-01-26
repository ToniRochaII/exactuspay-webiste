from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR
from .uk_tax_logic import UKTaxLogic

class UnitedKingdomPayrollStrategy:
    def __init__(self, payroll_calculator):
        self.calc = payroll_calculator
        self.employee = payroll_calculator.employee
        
        # Standard UK Tax Bands
        self.tax_bands = {
            'rUK': [
                (Decimal('37700.00'), Decimal('0.20')),
                (Decimal('125140.00'), Decimal('0.40')),
                (Decimal('999999999.00'), Decimal('0.45')),
            ]
        }

    def process_nuances(self):
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
        
        if "K" in tax_logic.prefix: 
            desc += " (Negative Allowance / Add to Pay)"
        else: 
            desc += " (Tax Free Allowance)"

        self.calc.results_dict['5500'] = adjustment_amount
        self.calc.register("Tax Adjustment", adjustment_amount, "5500", description=desc)

        # 4. PREPARE TAXABLE BASE
        gross_source = self.calc.results_dict.get('85000', Decimal('0.00'))
        adjusted_base = tax_logic.calculate_taxable_pay(gross_source, freq, period_num)
        self.calc.results_dict['86000'] = adjusted_base 
        
        # 5. ROUTING LOGIC
        # 6000 is TOTAL. 6001 is Standard Tax.
        managed_db_codes = ["6001", "6100", "6200", "6300", "6400"]
        
        current_code = tax_logic.clean_code
        active_db_code = None
        is_manual_calc = False

        # --- DETERMINE ACTIVE CALCULATION CODE ---
        if current_code == "BR":
            active_db_code = "6100"
        elif current_code == "D0":
            active_db_code = "6200"
        elif current_code == "D1":
            active_db_code = "6300"
        elif current_code == "NT":
            active_db_code = None 
        elif current_code == "0T":
            is_manual_calc = True
            active_db_code = "6001" # 0T Manual writes to 6001
        else:
            # Standard Codes (e.g. 1257L) use 6001
            active_db_code = "6001"

        # --- APPLY LOCKS & VALUES ---
        
        # Case A: Manual Calculation (0T)
        if is_manual_calc and current_code == "0T":
            bands = self.tax_bands['rUK']
            if "week" in freq.lower(): periods = Decimal("52")
            else: periods = Decimal("12")
            
            remaining = adjusted_base
            tax_calc = Decimal("0.00")
            prev_th = Decimal("0.00")
            
            for th, rate in bands:
                p_th = (th / periods).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                width = p_th - prev_th
                if remaining <= 0: break
                
                if th > Decimal('900000000'): taxable = remaining
                else: taxable = min(remaining, width)
                
                tax_calc += taxable * rate
                remaining -= taxable
                prev_th = p_th

            final_tax = tax_calc.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            
            # Register result to 6001 (NOT 6000)
            self.calc.results_dict['6001'] = -final_tax
            self.calc.register("PAYE Income Tax", -final_tax, "6001")
            
            # Lock 6001 and Block all others
            self.calc.explicit_overrides.add('6001')
            for code in managed_db_codes:
                if code != "6001":
                    self.calc.results_dict[code] = Decimal("0.00")
                    self.calc.explicit_overrides.add(code)

        # Case B: Database Engine Routing
        else:
            for code in managed_db_codes:
                if code == active_db_code:
                    # UNLOCK: Allow DB engine to calculate this code
                    self.calc.explicit_overrides.discard(code)
                else:
                    # BLOCK: Set to 0 and Lock it
                    self.calc.results_dict[code] = Decimal("0.00")
                    self.calc.explicit_overrides.add(code)