# File: Exactus/payroll/calculator/countries/gb/united_kingdom_payroll_strategy.py
from decimal import Decimal, ROUND_HALF_UP
from .uk_tax_logic import UKTaxLogic
import logging

logger = logging.getLogger(__name__)

class UnitedKingdomPayrollStrategy:
    def __init__(self, payroll_calculator):
        self.calc = payroll_calculator
        self.employee = payroll_calculator.employee
        
        # Standard UK Tax Bands (Annual) 2025/26
        self.tax_bands = {
            'rUK': [
                (Decimal('37700.00'), Decimal('0.20')),
                (Decimal('125140.00'), Decimal('0.40')),
                (Decimal('999999999.00'), Decimal('0.45')),
            ]
        }

    def process_nuances(self):
        print("DEBUG UnitedKingdomPayrollStrategy: Starting UK payroll calculation")
        
        # 1. FETCH DATA
        raw_code = getattr(self.employee, 'tax_info_03', '1257L') or '1257L'
        raw_basis = getattr(self.employee, 'tax_info_04', 'Cumulative') or 'Cumulative'
        ni_category = getattr(self.employee, 'tax_info_05', 'A') or 'A'
        ni_category = str(ni_category).upper().strip()
        
        print(f"DEBUG UnitedKingdomPayrollStrategy: Tax Code={raw_code}, Basis={raw_basis}, NI={ni_category}")
        
        # 2. INITIALIZE PARSER
        tax_logic = UKTaxLogic(raw_code, explicit_basis=raw_basis)
        freq = self.calc.period.frequency if self.calc.period else "monthly"
        period_num = int(self.calc.period.period_number) if self.calc.period else 1

        print(f"DEBUG UnitedKingdomPayrollStrategy: Frequency={freq}, Period={period_num}")
        
        # 3. REGISTER ALLOWANCE (5500 Series)
        adjustment_amount = tax_logic.get_period_allowance(freq, period=period_num)
        self.calc.results_dict['5500'] = adjustment_amount
        self.calc.register("Tax Adjustment", adjustment_amount, "5500")
        print(f"DEBUG UnitedKingdomPayrollStrategy: Allowance (5500) = £{adjustment_amount}")

        # 4. PREPARE TAXABLE BASE
        gross_source = self.calc.results_dict.get('85000', Decimal('0.00'))
        if gross_source == Decimal('0.00'):
            gross_source = self.calc.results_dict.get('5000', Decimal('0.00'))
        
        print(f"DEBUG UnitedKingdomPayrollStrategy: Gross source = £{gross_source}")
        
        # Current Period Taxable (86000)
        adjusted_base = tax_logic.calculate_taxable_pay(gross_source, freq, period_num)
        self.calc.results_dict['86000'] = adjusted_base 
        print(f"DEBUG UnitedKingdomPayrollStrategy: Taxable pay (86000) = £{adjusted_base}")
        
        # YTD Taxable (96001) - Cumulative Basis
        existing_ytd_taxable = self.calc.results_dict.get('96001', Decimal('0.00'))
        taxable_ytd = existing_ytd_taxable + adjusted_base
        self.calc.results_dict['96001'] = taxable_ytd
        print(f"DEBUG UnitedKingdomPayrollStrategy: YTD taxable (96001) = £{taxable_ytd}")
        
        # 5. INCOME TAX ROUTING
        self.calc.results_dict["6000"] = Decimal("0.00")
        self.calc.explicit_overrides.add("6000")

        current_code = tax_logic.clean_code
        print(f"DEBUG UnitedKingdomPayrollStrategy: Clean tax code = {current_code}")
        
        # CUMULATIVE CALCULATION FOR NORMAL TAX CODES
        if current_code not in ["BR", "D0", "D1", "NT"]:
            print("DEBUG UnitedKingdomPayrollStrategy: Using cumulative tax calculation")
            bands = self.tax_bands['rUK']
            total_annual_periods = Decimal("52") if "week" in freq.lower() else Decimal("12")
            
            remaining_ytd = taxable_ytd
            total_tax_due_ytd = Decimal("0.00")
            prev_th_ytd = Decimal("0.00")

            for annual_th, rate in bands:
                p_th_ytd = (annual_th * (Decimal(str(period_num)) / total_annual_periods)).quantize(Decimal("0.01"), ROUND_HALF_UP)
                width_ytd = p_th_ytd - prev_th_ytd
                
                if remaining_ytd <= 0: 
                    break
                
                if annual_th > Decimal('900000000'):  # Top band
                    taxable_in_band = remaining_ytd
                else:
                    taxable_in_band = min(remaining_ytd, width_ytd)
                    
                total_tax_due_ytd += taxable_in_band * rate
                print(f"DEBUG UnitedKingdomPayrollStrategy: Band tax: £{taxable_in_band} × {rate} = £{taxable_in_band * rate}")
                remaining_ytd -= taxable_in_band
                prev_th_ytd = p_th_ytd

            # Get tax paid YTD from previous periods
            tax_paid_to_date = self.calc.results_dict.get('16001', Decimal('0.00'))
            
            # Calculate this period's tax
            final_tax = (total_tax_due_ytd - tax_paid_to_date).quantize(Decimal("0.01"), ROUND_HALF_UP)
            
            print(f"DEBUG UnitedKingdomPayrollStrategy: Total tax due YTD = £{total_tax_due_ytd}")
            print(f"DEBUG UnitedKingdomPayrollStrategy: Tax paid to date = £{tax_paid_to_date}")
            print(f"DEBUG UnitedKingdomPayrollStrategy: This period tax = £{final_tax}")
            
            self.calc.results_dict['6001'] = -final_tax
            label = "PAYE Income Tax" if final_tax >= 0 else "PAYE Tax Refund"
            self.calc.register(label, -final_tax, "6001")
            self.calc.explicit_overrides.add('6001')
            
            # Store tax paid YTD for next period
            self.calc.results_dict['16001'] = total_tax_due_ytd
            
            # Zero out other tax codes
            for code in ["6100", "6200", "6300", "6400"]:
                self.calc.results_dict[code] = Decimal("0.00")
                self.calc.explicit_overrides.add(code)

        elif current_code == "NT":
            # No tax for NT code
            print("DEBUG UnitedKingdomPayrollStrategy: NT code - no tax")
            self.calc.results_dict['6001'] = Decimal("0.00")
            self.calc.register("PAYE Income Tax (NT)", Decimal("0.00"), "6001")
            self.calc.explicit_overrides.add('6001')
            
            for code in ["6100", "6200", "6300", "6400"]:
                self.calc.results_dict[code] = Decimal("0.00")
                self.calc.explicit_overrides.add(code)
                
        else:
            # Flat Rate Codes
            print(f"DEBUG UnitedKingdomPayrollStrategy: Using flat rate code {current_code}")
            flat_rate_map = {
                "BR": ("6100", Decimal("0.20")),
                "D0": ("6200", Decimal("0.40")),
                "D1": ("6300", Decimal("0.45")),
            }
            
            if current_code in flat_rate_map:
                target_code, rate = flat_rate_map[current_code]
                tax_amount = (adjusted_base * rate).quantize(Decimal("0.01"), ROUND_HALF_UP)
                self.calc.results_dict[target_code] = -tax_amount
                label = f"PAYE Tax ({current_code})"
                self.calc.register(label, -tax_amount, target_code)
                self.calc.explicit_overrides.add(target_code)
                
                print(f"DEBUG UnitedKingdomPayrollStrategy: Flat rate tax: £{adjusted_base} × {rate} = £{tax_amount}")
                
                # Store tax paid YTD
                existing_tax_paid = self.calc.results_dict.get('16001', Decimal('0.00'))
                self.calc.results_dict['16001'] = existing_tax_paid + tax_amount
            
            # Zero out other tax codes
            managed_tax_codes = ["6001", "6100", "6200", "6300", "6400"]
            for code in managed_tax_codes:
                if code not in self.calc.results_dict:
                    self.calc.results_dict[code] = Decimal("0.00")
                    self.calc.explicit_overrides.add(code)

        # 6. NATIONAL INSURANCE (7000 Series)
        ni_map = {
            'A': '7001', 'B': '7010', 'C': '7020', 'D': '7030', 'E': '7040', 
            'F': '7050', 'H': '7060', 'I': '7070', 'J': '7080', 'K': '7090', 
            'L': '7100', 'M': '7110', 'N': '7120', 'S': '7130', 'V': '7140',
            'Z': '7150', 'X': '7160'
        }
        
        active_ni_code = ni_map.get(ni_category, '7001')
        self.calc.active_ni_code = active_ni_code
        
        print(f"DEBUG UnitedKingdomPayrollStrategy: Active NI code = {active_ni_code}")
        
        self.calc.results_dict["7000"] = Decimal("0.00")
        self.calc.explicit_overrides.add("7000")
        
        # Enable only the active NI code
        for code in set(ni_map.values()):
            if code == active_ni_code:
                self.calc.explicit_overrides.discard(code)
            else:
                self.calc.results_dict[code] = Decimal("0.00")
                self.calc.explicit_overrides.add(code)

        # 7. EMPLOYER CONTRIBUTIONS (9000 Series)
        self.calc.results_dict["9000"] = Decimal("0.00")
        self.calc.explicit_overrides.add("9000")
        self.calc.explicit_overrides.discard("9001")
        
        print("DEBUG UnitedKingdomPayrollStrategy: Completed UK payroll calculation")