from decimal import Decimal, ROUND_FLOOR

class UKTaxLogic:
    def __init__(self, raw_code, explicit_basis="Cumulative"):
        """
        Initializes the parser with the tax code (e.g., '1257L', '1000N', 'SBR') 
        and the tax basis (e.g., 'Cumulative' or 'Week1/Month1').
        """
        self.raw_code = str(raw_code).upper().strip()
        self.basis = explicit_basis.lower()
        
        # Flags
        self.is_scottish = False
        self.is_welsh = False
        self.is_k_code = False
        
        # Parsed Data
        self.code_number = 0
        self.suffix = ""
        
        self._parse_code()

    def _parse_code(self):
        """
        Robustly extracts prefixes, numbers, and suffixes.
        Handles: S1257L, C1257L, K100, 1000N, BR, D0, etc.
        """
        code = self.raw_code
        
        # 1. Handle Country Prefixes
        if code.startswith('S'):
            self.is_scottish = True
            code = code[1:]
        elif code.startswith('C'):
            self.is_welsh = True
            code = code[1:]
            
        # 2. Handle Zero/Special Codes immediately
        # These are codes that are purely letters or fixed combinations
        special_codes = ['BR', 'D0', 'D1', 'D2', 'NT', '0T', '0L']
        if code in special_codes:
            self.suffix = code
            self.code_number = 0
            return

        # 3. Handle 'K' Prefix (Tax on additional income)
        if code.startswith('K'):
            self.is_k_code = True
            code = code[1:]
            
        # 4. Separate Number and Suffix
        # Example: '1000N' -> Number: '1000', Suffix: 'N'
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
        """
        Computes the total annual monetary amount the tax code represents.
        """
        # 1. Zero Allowance Check
        # If the parsing identified it as a special zero code, return 0.
        if self.suffix in ['BR', 'D0', 'D1', 'D2', 'NT', '0T', '0L']:
            return Decimal("0.00")
            
        # 2. Safety Check: If we have no number (and it's not a special code), default to 0
        if self.code_number == 0:
            return Decimal("0.00")

        # 3. Standard Calculation: (Code * 10) + 9
        # This applies to:
        # - L (Standard)
        # - M (Marriage Allowance Received)
        # - N (Marriage Allowance Transferred) [e.g. 1000N]
        # - T (Review needed)
        # - Y (Over 75)
        # - K (Negative allowance, but magnitude is calculated same way)
        total = (self.code_number * 10) + 9
        return Decimal(str(total))




    def get_period_allowance(self, frequency, period=1):
        """
        Returns the specific allowance for the given period.
        K codes return a NEGATIVE value (adding to taxable pay).
        Standard codes return a POSITIVE value (subtracting from taxable pay).
        """
        annual_total = self.get_annual_allowance()
        
        # Determine frequency divisor
        if "week" in str(frequency).lower():
            divisor = Decimal("52")
        else:
            divisor = Decimal("12")

        # K codes add to taxable pay (Negative Allowance)
        # Standard codes reduce taxable pay (Positive Allowance)
        multiplier = Decimal("-1.00") if self.is_k_code else Decimal("1.00")
        
        # Check Basis
        is_non_cumulative = any(x in self.basis for x in ["week1", "month1", "w1", "m1"])

        if is_non_cumulative:
            # Week 1 / Month 1: Use exactly 1 chunk of the allowance
            period_allowance = (annual_total / divisor)
        else:
            # Cumulative: Use the allowance up to the current period
            period_allowance = (annual_total / divisor) * Decimal(str(period))

        # Apply Sign and Round Down (HMRC Standard)
        final_adjustment = (period_allowance * multiplier).quantize(Decimal("0.01"), rounding=ROUND_FLOOR)
        
        return final_adjustment