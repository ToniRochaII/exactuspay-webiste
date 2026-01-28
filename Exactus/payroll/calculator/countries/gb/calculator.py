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
        
        ni_category = getattr(self.employee, 'tax_info_05', 'A') or 'A'
        ni_category = str(ni_category).upper().strip()
        
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
        
        # ====================================================
        # 5. INCOME TAX ROUTING (6000 Series)
        # ====================================================
        managed_tax_codes = ["6001", "6100", "6200", "6300", "6400"]
        current_code = tax_logic.clean_code
        active_tax_code = None
        is_manual_calc = False

        if current_code == "BR": active_tax_code = "6100"
        elif current_code == "D0": active_tax_code = "6200"
        elif current_code == "D1": active_tax_code = "6300"
        elif current_code == "NT": active_tax_code = None 
        elif current_code == "0T":
            is_manual_calc = True
            active_tax_code = "6001"
        else:
            active_tax_code = "6001"

        self.calc.results_dict["6000"] = Decimal("0.00")
        self.calc.explicit_overrides.add("6000")

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
            
            self.calc.results_dict['6001'] = -final_tax
            self.calc.register("PAYE Income Tax", -final_tax, "6001")
            self.calc.explicit_overrides.add('6001')
            for code in managed_tax_codes:
                if code != "6001":
                    self.calc.results_dict[code] = Decimal("0.00")
                    self.calc.explicit_overrides.add(code)
        else:
            for code in managed_tax_codes:
                if code == active_tax_code:
                    self.calc.explicit_overrides.discard(code)
                else:
                    self.calc.results_dict[code] = Decimal("0.00")
                    self.calc.explicit_overrides.add(code)

        # ====================================================
        # 6. NATIONAL INSURANCE ROUTING (7000 Series)
        # ====================================================
        ni_map = {
            'A': '7001', 
            'B': '7010', # <--- STRICT RULE APPLIED: B IS 7010
            'C': '7003', 'D': '7030', 'E': '7040', 
            'F': '7050', 'H': '7060', 'I': '7070','J': '7080',  'K': '7090', 
            'L': '7100', 'M': '7110', 'N': '7120', 'S': '7130', 'V': '7140',
            'Z': '7150', 'X': '7160'
        }
        active_ni_code = ni_map.get(ni_category, '7001')
        self.calc.active_ni_code = active_ni_code

        # Block Reporting Code
        self.calc.results_dict["7000"] = Decimal("0.00")
        self.calc.explicit_overrides.add("7000")
        
        # Manage Calculation Codes
        # Ensure Active Employee NI is unlocked.
        # Ensure 7010 is unlocked (it acts as Employer NI usually, but here it is also Employee Cat B)
        all_ni_codes = set(ni_map.values())
        all_ni_codes.add("7010") 

        for code in all_ni_codes:
            if code == active_ni_code:
                self.calc.explicit_overrides.discard(code) # UNLOCK Employee NI
            elif code == "7010" and ni_category != 'X':
                self.calc.explicit_overrides.discard(code) # UNLOCK Employer NI/Cat B
            else:
                self.calc.results_dict[code] = Decimal("0.00")
                self.calc.explicit_overrides.add(code) # LOCK others

        # ====================================================
        # 7. OTHER DEDUCTIONS ROUTING (9000 Series)
        # ====================================================
        self.calc.results_dict["9000"] = Decimal("0.00")
        self.calc.explicit_overrides.add("9000")
        
        managed_other_codes = ["9001"]
        active_other_code = "9001"

        for code in managed_other_codes:
            if code == active_other_code:
                self.calc.explicit_overrides.discard(code)
            else:
                self.calc.results_dict[code] = Decimal("0.00")
                self.calc.explicit_overrides.add(code)