from decimal import Decimal, ROUND_UP, ROUND_DOWN, ROUND_HALF_UP

class TaxEngine:
    """
    Pure Logic Engine. Accepts an Amount and a Rule Object. Returns Tax.
    """

    @staticmethod
    def _round(value, method, precision=Decimal('1')):
        value = Decimal(str(value))
        if method == 'Round up':
            return value.quantize(precision, rounding=ROUND_UP)
        elif method == 'Round down':
            return value.quantize(precision, rounding=ROUND_DOWN)
        return value

    @classmethod
    def calculate_progressive_tax(cls, taxable_amount, rule):
        """
        Calculates tax by dynamically iterating through rule.bracket_XX fields.
        """
        # 1. Round the Input Base
        amount_remaining = cls._round(taxable_amount, rule.rounding_base)
        total_tax = Decimal("0.00")
        
        # 2. Iterate through Bands (00 to 15)
        for i in range(16):
            # Dynamic field lookup
            limit_field = f"bracket_{i:02d}"
            rate_field = f"rate_{i:02d}"
            
            # Safety break if fields don't exist
            if not hasattr(rule, limit_field): 
                break

            band_width = getattr(rule, limit_field)
            rate = getattr(rule, rate_field)
            
            # Apply Rounding to Bracket Definition
            band_width = cls._round(band_width, rule.rounding_bracket)

            # Determine Taxable Chunk for this Band
            # If band_width is 0, it means "Infinity" (the rest of the salary)
            if band_width > 0:
                taxable_chunk = min(amount_remaining, band_width)
            else:
                taxable_chunk = amount_remaining

            # Calculate Tax for this Chunk
            if taxable_chunk > 0:
                tax_chunk = taxable_chunk * (rate / Decimal("100.00"))
                total_tax += tax_chunk
                
                # Reduce remaining amount to process in next band
                amount_remaining -= taxable_chunk
            
            # If no money left to tax, stop
            if amount_remaining <= 0:
                break

        # 3. Final Rounding
        return cls._round(total_tax, rule.rounding_taxed, Decimal('0.01'))