# Exactus/payroll/services/calculation_base_service.py
from decimal import Decimal, ROUND_UP, ROUND_DOWN, ROUND_HALF_UP
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

class CalculationBaseService:
    """
    Service to fetch and apply CalculationBase rules for payroll calculations.
    """
    
    @staticmethod
    def get_calculation_base(period, element_code, element_base_code=None):
        """
        Get appropriate CalculationBase for a period and element.
        
        Args:
            period: PayrollPeriod instance
            element_code: Code of the element (e.g., '6100' for tax)
            element_base_code: Base element code (e.g., '6000' for tax-free allowance)
        
        Returns:
            CalculationBase instance or None
        """
        from Exactus.payroll.models import CalculationBase
        from Exactus.regulations.models import Element
        
        try:
            # Get the regulation from payroll
            regulation = period.payroll.regulation
            
            # Get the element
            element = Element.objects.filter(
                country=period.payroll.country,
                element_code=element_code
            ).first()
            
            if not element:
                logger.warning(f"Element {element_code} not found for country {period.payroll.country}")
                return None
            
            # Build query
            query = Q(regulations=regulation, element=element)
            
            # If base element is specified, filter by it
            if element_base_code:
                base_element = Element.objects.filter(
                    country=period.payroll.country,
                    element_code=element_base_code
                ).first()
                if base_element:
                    query &= Q(element_base=base_element)
            
            # Get calculation base
            calculation_base = CalculationBase.objects.filter(query).first()
            
            if calculation_base:
                logger.debug(f"Found CalculationBase {calculation_base.id} for {element_code}")
            
            return calculation_base
            
        except Exception as e:
            logger.error(f"Error fetching calculation base: {e}")
            return None
    
    @staticmethod
    def calculate_with_base(base_id, amount, rounding_base='None', 
                           rounding_bracket='None', rounding_taxed='None'):
        """
        Calculate tax/contribution using bracket system from CalculationBase.
        
        This replicates the logic from your previous income_tax function.
        """
        from Exactus.regulations.models import CalculationBase
        
        try:
            base = CalculationBase.objects.get(id=base_id)
            
            # Convert amount to Decimal
            amount_decimal = Decimal(str(amount))
            
            # Define rounding functions
            def apply_base_rounding(value, rounding_type):
                if rounding_type == 'round up':
                    return value.quantize(Decimal('1'), rounding=ROUND_UP)
                elif rounding_type == 'round down':
                    return value.quantize(Decimal('1'), rounding=ROUND_DOWN)
                else:
                    return value
            
            def apply_bracket_rounding(value, rounding_type):
                if rounding_type == 'round up':
                    return value.quantize(Decimal('1'), rounding=ROUND_UP)
                elif rounding_type == 'round down':
                    return value.quantize(Decimal('1'), rounding=ROUND_DOWN)
                else:
                    return value
            
            def apply_taxed_rounding(value, rounding_type):
                if rounding_type == 'round up':
                    return value.quantize(Decimal('0.01'), rounding=ROUND_UP)
                elif rounding_type == 'round down':
                    return value.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                else:
                    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Get bracket values as list
            brackets = [
                base.bracket_00 or Decimal('0'),
                base.bracket_01 or Decimal('0'),
                base.bracket_02 or Decimal('0'),
                base.bracket_03 or Decimal('0'),
                base.bracket_04 or Decimal('0'),
                base.bracket_05 or Decimal('0'),
                base.bracket_06 or Decimal('0'),
                base.bracket_07 or Decimal('0'),
                base.bracket_08 or Decimal('0'),
                base.bracket_09 or Decimal('0'),
                base.bracket_10 or Decimal('0'),
                base.bracket_11 or Decimal('0'),
                base.bracket_12 or Decimal('0'),
                base.bracket_13 or Decimal('0'),
                base.bracket_14 or Decimal('0'),
                base.bracket_15 or Decimal('0'),
            ]
            
            # Get rates as list
            rates = [
                base.rate_00 or Decimal('0'),
                base.rate_01 or Decimal('0'),
                base.rate_02 or Decimal('0'),
                base.rate_03 or Decimal('0'),
                base.rate_04 or Decimal('0'),
                base.rate_05 or Decimal('0'),
                base.rate_06 or Decimal('0'),
                base.rate_07 or Decimal('0'),
                base.rate_08 or Decimal('0'),
                base.rate_09 or Decimal('0'),
                base.rate_10 or Decimal('0'),
                base.rate_11 or Decimal('0'),
                base.rate_12 or Decimal('0'),
                base.rate_13 or Decimal('0'),
                base.rate_14 or Decimal('0'),
                base.rate_15 or Decimal('0'),
            ]
            
            # Apply base rounding to input amount
            rounded_amount = apply_base_rounding(amount_decimal, rounding_base)
            
            # Calculate progressive tax
            total_tax = Decimal('0')
            accumulated_brackets = Decimal('0')
            
            for i, (bracket, rate) in enumerate(zip(brackets, rates)):
                if bracket == 0:
                    continue
                    
                # Apply bracket rounding
                rounded_bracket = apply_bracket_rounding(bracket, rounding_bracket)
                
                # Calculate taxable amount in this bracket
                taxable_in_bracket = max(
                    Decimal('0'),
                    min(
                        rounded_amount - accumulated_brackets,
                        rounded_bracket
                    )
                )
                
                if taxable_in_bracket > 0:
                    tax_in_bracket = taxable_in_bracket * (rate / Decimal('100'))
                    total_tax += apply_taxed_rounding(tax_in_bracket, rounding_taxed)
                
                accumulated_brackets += rounded_bracket
                
                # If we've exceeded all brackets, calculate remaining at last rate
                if rounded_amount <= accumulated_brackets:
                    break
            
            # Handle amount exceeding all defined brackets
            if rounded_amount > accumulated_brackets:
                remaining_amount = rounded_amount - accumulated_brackets
                # Use the last non-zero rate for remaining amount
                last_rate = next((rate for rate in reversed(rates) if rate > 0), Decimal('0'))
                if last_rate > 0:
                    tax_on_remainder = remaining_amount * (last_rate / Decimal('100'))
                    total_tax += apply_taxed_rounding(tax_on_remainder, rounding_taxed)
            
            return total_tax
            
        except CalculationBase.DoesNotExist:
            logger.error(f"CalculationBase {base_id} not found")
            return Decimal('0')
        except Exception as e:
            logger.error(f"Error in calculation: {e}")
            return Decimal('0')