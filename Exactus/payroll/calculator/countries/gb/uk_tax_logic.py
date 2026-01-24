# Exactus/payroll/calculator/countries/gb/uk_tax_logic.py
import re
from decimal import Decimal, ROUND_HALF_UP

class UKTaxCodeParser:
    def __init__(self, code_str, explicit_basis=None):
        self.raw_code = str(code_str).upper().strip()
        self.explicit_basis = str(explicit_basis).upper().strip() if explicit_basis else ""
        self.annual_allowance = Decimal("0.00")
        self.is_cumulative = True 
        
        self._parse()

    def _parse(self):
        code = self.raw_code

        # 1. Check for Non-Cumulative Flags (Week 1 / Month 1)
        if (code.endswith("W1") or code.endswith("M1") or code.endswith("X") or 
            "WEEK" in self.explicit_basis or "MONTH 1" in self.explicit_basis):
            self.is_cumulative = False
            code = code.replace("W1", "").replace("M1", "").replace("X", "").strip()

        # 2. Parse Code Types
        if code in ["BR", "D0", "D1", "0T"]:
            self.annual_allowance = Decimal("0.00")
        elif code == "NT":
            self.annual_allowance = Decimal("999999999.00")
        elif code.startswith("K"):
            # K codes are negative allowances (add to taxable pay)
            self.annual_allowance = self._extract_numbers(code) * Decimal("-10.00")
        elif re.search(r'[LMNPTY]', code):
            # Standard: 1257L -> 1257 * 10 = 12570
            self.annual_allowance = self._extract_numbers(code) * Decimal("10.00")

    def _extract_numbers(self, text):
        digits = re.findall(r'\d+', text)
        return Decimal(digits[0]) if digits else Decimal("0")

    def get_period_allowance(self, frequency="monthly"):
        # Returns 1047.50 for 1257L Monthly
        periods = Decimal("12")
        if "week" in frequency.lower():
            periods = Decimal("52") # Simplified for example
        
        return (self.annual_allowance / periods).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)