import re
from decimal import Decimal, ROUND_HALF_UP

class UKTaxLogic:
    def __init__(self, code_str, explicit_basis=None):
        self.raw_code = str(code_str).upper().strip()
        self.explicit_basis = str(explicit_basis).upper().strip() if explicit_basis else ""
        self.is_cumulative = True
        self.prefix = ""
        self.numeric_part = 0
        self.clean_code = ""
        
        self._parse()

    def _parse(self):
        code = self.raw_code
        if (code.endswith("W1") or code.endswith("M1") or code.endswith("X") or 
            "WEEK 1" in self.explicit_basis or "MONTH 1" in self.explicit_basis):
            self.is_cumulative = False
            code = code.replace("W1", "").replace("M1", "").replace("X", "").strip()
            
        if code.startswith("K"):
            self.prefix = "K"
        elif code.startswith("S") or code.startswith("C"):
             if any(char.isdigit() for char in code):
                 self.prefix = code[0]

        self.clean_code = code
        if self.prefix in ['S', 'C'] and code.startswith(self.prefix):
            self.clean_code = code[1:]

        numeric_match = re.search(r'\d+', self.clean_code)
        if numeric_match:
            self.numeric_part = int(numeric_match.group(0))

    def _get_annual_adjustment(self):
        base = self.clean_code
        if base in ["BR", "D0", "D1", "0T", "NT", "S0T", "C0T"]:
            return Decimal("0.00")
        return (Decimal(self.numeric_part) * Decimal("10.00")) + Decimal("9.00")

    def get_period_allowance(self, frequency="monthly", period=1):
        annual = self._get_annual_adjustment()
        if annual == 0: return Decimal("0.00")
        
        if "week" in frequency.lower(): total = Decimal("52")
        else: total = Decimal("12")

        eff = Decimal("1") if not self.is_cumulative else Decimal(period)
        adj = (annual / total) * eff
        return adj.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_taxable_pay(self, gross_pay, frequency="monthly", period=1):
        adj = self.get_period_allowance(frequency, period)
        gross = Decimal(str(gross_pay))
        if self.prefix == "K" or self.clean_code.startswith("K"):
            return gross + adj
        else:
            return max(Decimal("0.00"), gross - adj)