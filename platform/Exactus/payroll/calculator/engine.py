from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING

class TaxEngine:
    @staticmethod
    def calculate_progressive_tax(base_value, rule):
        """
        Calculates tax based on the CalculationBase rule (from DB),
        applying granular rounding at:
        1. Global Base Level
        2. Per-Bracket Taxable Portion Level
        3. Per-Bracket Tax Result Level
        4. Global Final Tax Level
        """
        
        # 1. Global Base Rounding (The "Set up" section)
        # We round the input amount (e.g. 86000) before starting.
        remaining_base = TaxEngine.apply_rounding(
            base_value, 
            rule.rounding_base, 
            rule.rounding_base_decimals
        )
        
        total_tax = Decimal("0.00")
        
        # Loop through all 16 brackets (00 to 15)
        for i in range(16):
            code = f"{i:02d}"
            
            # Fetch Bracket Config
            bracket_limit = getattr(rule, f'bracket_{code}')
            rate = getattr(rule, f'rate_{code}')
            
            # Fetch Per-Bracket Rounding Config
            # "Bracket" rounding = Rounding the taxable income chunk
            logic_bracket = getattr(rule, f'round_bracket_logic_{code}')
            dec_bracket = getattr(rule, f'round_bracket_dec_{code}')
            
            # "Result" rounding = Rounding the calculated tax for this chunk
            logic_result = getattr(rule, f'round_result_logic_{code}')
            dec_result = getattr(rule, f'round_result_dec_{code}')
            
            # If bracket has no data, skip
            if (bracket_limit is None or bracket_limit == 0) and (rate is None or rate == 0):
                continue
            
            # Convert Rate to decimal (e.g. 20 -> 0.20)
            # Assumption: If user enters "20" for 20%, we need to divide by 100.
            # If user enters "0.20", we use as is. 
            # Check if rate > 1 (implies percentage integer)
            effective_rate = Decimal(rate)
            if effective_rate > 1:
                effective_rate = effective_rate / Decimal("100.00")
            
            # Determine how much money falls into this bracket
            taxable_chunk = Decimal("0.00")
            
            if bracket_limit > 0:
                # If there is a limit, fill it up to the limit
                if remaining_base >= bracket_limit:
                    taxable_chunk = bracket_limit
                    remaining_base -= bracket_limit
                else:
                    taxable_chunk = remaining_base
                    remaining_base = Decimal("0.00")
            else:
                # If limit is 0 (or infinite), take everything remaining
                taxable_chunk = remaining_base
                remaining_base = Decimal("0.00")
            
            # SKIP if no money in this bracket
            if taxable_chunk <= 0:
                continue

            # 2. Apply "Bracket" Rounding (Round the taxable chunk)
            taxable_chunk = TaxEngine.apply_rounding(taxable_chunk, logic_bracket, dec_bracket)
            
            # Calculate Tax for this bracket
            bracket_tax = taxable_chunk * effective_rate
            
            # 3. Apply "Result" Rounding (Round the tax)
            bracket_tax = TaxEngine.apply_rounding(bracket_tax, logic_result, dec_result)
            
            total_tax += bracket_tax

            # Optimization: If no base left and we handled the infinite bracket, break
            if remaining_base <= 0:
                break
        
        # 4. Global Final Tax Rounding
        final_tax = TaxEngine.apply_rounding(
            total_tax, 
            rule.rounding_taxed, 
            rule.rounding_taxed_decimals
        )
        
        return final_tax

    @staticmethod
    def apply_rounding(value, logic_str, decimals):
        """
        Helper to apply Round Up/Down/Standard based on string from DB.
        """
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
            
        if not logic_str or logic_str == 'None':
            # Default to Standard Half Up if not specified, or just quantize
            rounding_mode = ROUND_HALF_UP
        elif 'down' in logic_str.lower():
            rounding_mode = ROUND_FLOOR
        elif 'up' in logic_str.lower():
            rounding_mode = ROUND_CEILING
        else:
            rounding_mode = ROUND_HALF_UP

        # Create the exponent for quantization (e.g., '0.01' for 2 decimals)
        if decimals == 0:
            exp = Decimal("1")
        else:
            exp = Decimal("1." + "0" * decimals)

        return value.quantize(exp, rounding=rounding_mode)