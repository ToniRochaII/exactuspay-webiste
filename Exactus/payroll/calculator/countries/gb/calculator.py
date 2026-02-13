from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR
import logging

logger = logging.getLogger(__name__)

# =========================================================
# 1. INTERNAL LOGIC CLASS (Merged here to prevent Import Errors)
# =========================================================
class UKTaxLogic:
    def __init__(self, raw_code, explicit_basis="Cumulative"):
        self.raw_code = str(raw_code).upper().strip()
        self.basis = explicit_basis.lower()
        
        self.is_scottish = False
        self.is_welsh = False
        self.is_k_code = False
        
        self.code_number = 0
        self.suffix = ""
        
        self._parse_code()

    def _parse_code(self):
        code = self.raw_code
        
        # 1. Handle Country Prefixes
        if code.startswith('S'):
            self.is_scottish = True
            code = code[1:]
        elif code.startswith('C'):
            self.is_welsh = True
            code = code[1:]
            
        # 2. Handle Zero/Special Codes
        special_codes = ['BR', 'D0', 'D1', 'D2', 'NT', '0T', '0L']
        if code in special_codes:
            self.suffix = code
            self.code_number = 0
            return

        # 3. Handle 'K' Prefix
        if code.startswith('K'):
            self.is_k_code = True
            code = code[1:]
            
        # 4. Separate Number and Suffix
        number_str = ""
        suffix_str = ""
        
        for char in code:
            if char.isdigit():
                number_str += char
            else:
                suffix_str += char
        
        self.code_number = int(number_str) if number_str else 0
        self.suffix = suffix_str.strip()

    def get_annual_allowance(self):
        if self.suffix in ['BR', 'D0', 'D1', 'D2', 'NT', '0T', '0L']:
            return Decimal("0.00")
            
        if self.code_number == 0:
            return Decimal("0.00")

        # Standard Calculation: (Code * 10) + 9
        total = (self.code_number * 10) + 9
        return Decimal(str(total))

    def get_period_allowance(self, frequency, period=1):
        annual_total = self.get_annual_allowance()
        
        if "week" in str(frequency).lower():
            divisor = Decimal("52")
        else:
            divisor = Decimal("12")

        multiplier = Decimal("-1.00") if self.is_k_code else Decimal("1.00")
        is_non_cumulative = any(x in self.basis for x in ["week1", "month1", "w1", "m1"])

        if is_non_cumulative:
            period_allowance = (annual_total / divisor)
        else:
            period_allowance = (annual_total / divisor) * Decimal(str(period))

        final_adjustment = (period_allowance * multiplier).quantize(Decimal("0.01"), rounding=ROUND_FLOOR)
        return final_adjustment

# =========================================================
# 2. MAIN STRATEGY CLASS
# =========================================================
class UnitedKingdomPayrollStrategy:
    def __init__(self, payroll_calculator):
        self.calc = payroll_calculator
        self.employee = payroll_calculator.employee
        self.period = payroll_calculator.period

    def process_nuances(self):
        # DEBUG MARKER: Watch your terminal for this!
        print(f"🔥🔥🔥 UK STRATEGY LOADED: Code {self.employee.tax_info_03} 🔥🔥🔥")

        # 1. FETCH EMPLOYEE DATA
        raw_code = getattr(self.employee, 'tax_info_03', '1257L') or '1257L'
        raw_basis = getattr(self.employee, 'tax_info_04', 'Cumulative') or 'Cumulative'
        ni_category = getattr(self.employee, 'tax_info_05', 'A') or 'A'
        
        # 2. INITIALIZE LOGIC (Using the internal class)
        tax_logic = UKTaxLogic(raw_code, explicit_basis=raw_basis)
        
        freq = self.period.frequency if self.period else "monthly"
        period_num = self.period.period_number if self.period else 1
        is_cumulative = not any(x in raw_basis.lower() for x in ["week1", "month1", "w1", "m1"])
        
        periodic_gross = self.calc.results_dict.get('5000', Decimal('0.00'))
        
        # --- PROCESS SECTIONS ---
        self._process_income_tax(tax_logic, freq, period_num, is_cumulative, periodic_gross)
        self._process_national_insurance(ni_category, period_num, is_cumulative)
        self._process_employer_ni(period_num, is_cumulative)
        self._process_apprenticeship_levy(period_num)

    def _process_income_tax(self, tax_logic, freq, period_num, is_cumulative, periodic_gross):
        # [STEP 1] Calculate Allowance
        tax_free_allowance = tax_logic.get_period_allowance(freq, period=period_num)
        print(f"   -> Allowance Calculated: £{tax_free_allowance}")
        
        clean_code = tax_logic.raw_code
        if tax_logic.is_scottish or tax_logic.is_welsh:
            clean_code = clean_code[1:]

        # Determine Target Codes
        base_suffix = "001"
        tax_target_code = "6001"
        if clean_code.startswith("BR"):
            base_suffix = "100"; tax_target_code = "6100"
        elif clean_code.startswith("D0"):
            base_suffix = "200"; tax_target_code = "6200"
        elif clean_code.startswith("D1"):
            base_suffix = "300"; tax_target_code = "6300"

        prefix = "96" if is_cumulative else "86"
        taxable_base_code = f"{prefix}{base_suffix}"

        # [STEP 2] Apply Allowance
        taxable_source = self.calc.results_dict.get('86000', Decimal('0.00'))
        adjusted_base = taxable_source - tax_free_allowance
        
        # Prevent negative taxable pay (Standard L/N/M codes)
        if not tax_logic.is_k_code and adjusted_base < 0:
            adjusted_base = Decimal("0.00")
            
        self.calc.results_dict[taxable_base_code] = adjusted_base
        print(f"   -> Taxable Base (Code {taxable_base_code}): £{adjusted_base}")
        
        # [STEP 3] Calculate Tax
        tax_amount = self._calculate_tax_with_limit(
            tax_target_code, adjusted_base, period_num, is_cumulative, periodic_gross
        )
        
        self.calc.results_dict[tax_target_code] = tax_amount
        self.calc.register(f"Income Tax ({tax_logic.raw_code})", tax_amount, tax_target_code)
        
        # Block engine from doubling up
        for i in range(6001, 6400):
            self.calc.explicit_overrides.add(str(i))

    def _process_national_insurance(self, ni_category, period_num, is_cumulative):
        mapping = {"B": "7010", "C": "7020", "H": "7030", "J": "7040", "M": "7050", "Z": "7060"}
        target_ni_code = mapping.get(ni_category.upper(), "7001")
        self.calc.active_ni_code = target_ni_code
        
        prefix = "97" if is_cumulative else "87"
        ni_base_code = f"{prefix}000"
        ni_base_val = self.calc.results_dict.get('87000', Decimal('0.00'))
        self.calc.results_dict[ni_base_code] = ni_base_val

        self._calculate_and_register(target_ni_code, ni_base_val, period_num, is_cumulative, f"NI Category {ni_category}")

        for i in range(7001, 7400):
            self.calc.explicit_overrides.add(str(i))

    def _process_employer_ni(self, period_num, is_cumulative):
        prefix = "99" if is_cumulative else "89"
        er_base_code = f"{prefix}000"
        er_base_val = self.calc.results_dict.get('89000', Decimal('0.00'))
        self.calc.results_dict[er_base_code] = er_base_val
        self._calculate_and_register("9000", er_base_val, period_num, is_cumulative, "Employer NI")
        self.calc.explicit_overrides.add("9000")

    def _process_apprenticeship_levy(self, period_num):
        ni_gross = self.calc.results_dict.get('87000', Decimal('0.00'))
        levy_amount = -(ni_gross * Decimal("0.005")).quantize(Decimal("0.01"), ROUND_HALF_UP)
        target_code = "9001"
        self.calc.results_dict[target_code] = levy_amount
        self.calc.register("Apprenticeship Levy", levy_amount, target_code)
        self.calc.explicit_overrides.add(target_code)

    def _calculate_tax_with_limit(self, target_code, base_val, period_num, is_cumulative, periodic_gross):
        raw_tax = self._get_engine_result(target_code, base_val, period_num, is_cumulative)
        max_tax = periodic_gross * Decimal("0.50")
        final_tax = min(abs(raw_tax), max_tax)
        return -abs(final_tax.quantize(Decimal("0.01"), ROUND_HALF_UP))

    def _calculate_and_register(self, target_code, base_val, period_num, is_cumulative, label):
        amount = self._get_engine_result(target_code, base_val, period_num, is_cumulative)
        result = -abs(amount.quantize(Decimal("0.01"), ROUND_HALF_UP))
        self.calc.results_dict[target_code] = result
        self.calc.register(label, result, target_code)
        self.calc.explicit_overrides.add(target_code)

    from decimal import Decimal

    def _get_engine_result(self, target_code, base_val, period_num, is_cumulative):
        from Exactus.payroll.calculator.engine import TaxEngine
        from Exactus.calculationbase.models import CalculationBase

        rule = CalculationBase.objects.filter(
            element__element_code=target_code,
            regulations=self.period.payroll.regulation,
            base_frequency=self.period.frequency,
        ).first()

        if not rule:
            return Decimal("0.00")

        # TaxEngine signature is: calculate_progressive_tax(base_value, rule)
        return TaxEngine.calculate_progressive_tax(base_val, rule)
