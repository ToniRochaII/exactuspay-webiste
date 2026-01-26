import re
from decimal import Decimal, ROUND_HALF_UP

class UKTaxLogic:
    """
    Parses UK Tax Codes to determine the Tax Free Allowance.
    Strictly handles Logic (Parsing), not Rates.
    """

    def __init__(self, code_str, explicit_basis=None):
        self.raw_code = str(code_str).upper().strip()
        self.explicit_basis = str(explicit_basis).upper().strip() if explicit_basis else ""
        self.is_cumulative = True
        self.prefix = ""
        self.numeric_part = 0
        self.clean_code = ""  # Code without W1/M1 flags
        
        self._parse()

    def _parse(self):
        code = self.raw_code

        # 1. Check for Non-Cumulative Flags
        if (code.endswith("W1") or code.endswith("M1") or code.endswith("X") or 
            "WEEK 1" in self.explicit_basis or "MONTH 1" in self.explicit_basis):
            self.is_cumulative = False
            code = code.replace("W1", "").replace("M1", "").replace("X", "").strip()
            
        self.clean_code = code

        # 2. Identify Prefix
        prefix_match = re.match(r'^(S|C|K|SK|CK)', code)
        if prefix_match:
            self.prefix = prefix_match.group(1)

        # 3. Extract Numeric Part
        numeric_match = re.search(r'\d+', code)
        if numeric_match:
            self.numeric_part = int(numeric_match.group(0))

    def _get_annual_adjustment(self):
        """
        Returns Annual Tax Free Allowance.
        BR, D0, D1, 0T have 0 allowance.
        """
        if self.clean_code in ["BR", "D0", "D1", "0T"]:
            return Decimal("0.00")
        
        if self.clean_code == "NT":
            return Decimal("0.00") 
            
        # Standard: (Code * 10) + 9
        return (Decimal(self.numeric_part) * Decimal("10.00")) + Decimal("9.00")

    def get_period_allowance(self, frequency="monthly", period=1):
        annual_total = self._get_annual_adjustment()
        
        if "week" in frequency.lower():
            total_periods = Decimal("52")
        else:
            total_periods = Decimal("12")

        effective_period = Decimal("1") if not self.is_cumulative else Decimal(period)
        adjustment = (annual_total / total_periods) * effective_period
        
        return adjustment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_taxable_pay(self, gross_pay_to_date, frequency="monthly", period=1):
        adjustment = self.get_period_allowance(frequency, period)
        gross_pay = Decimal(str(gross_pay_to_date))

        if "K" in self.prefix:
            return gross_pay + adjustment
        else:
            taxable = gross_pay - adjustment
            return max(Decimal("0.00"), taxable)