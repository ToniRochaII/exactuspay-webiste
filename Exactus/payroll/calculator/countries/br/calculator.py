from decimal import Decimal
from typing import Dict, List, Any
from django.db.models import Sum, Q

from Exactus.payroll.calculator.base import BasePayrollCalculator
from Exactus.calculationbase.models import CalculationBase
from Exactus.pdcodes.models import PDcode 
from Exactus.compensation.models import CompensationComponent

class BRPayrollCalculator(BasePayrollCalculator):
    """
    Brazil Payroll Calculator
    Uses Standardized Schema:
    - 1000-1999: Payments (Earnings)
    - 6000-6999: Income Tax (IRRF)
    - 7000-7999: Social Security (INSS)
    """

    # Define Constants for Tax Tables (Elements)
    CODE_IRRF_TABLE = '6001'
    CODE_INSS_TABLE = '7001'

    def __init__(self, country, tax_year, period, employees):
        super().__init__(country, tax_year, period, employees)
        self.rules = self.load_regulation_rules()

    def load_regulation_rules(self) -> Dict[str, Any]:
        """
        Loads the Regulation Base matrix (Tax Tables).
        Expects Elements with codes in ranges 6000-7999 for taxes.
        """
        regulation = self.period.payroll.regulation
        
        # We fetch ALL rules for this regulation version
        bases = CalculationBase.objects.filter(
            country=self.country,
            regulations=regulation
        ).select_related('element')
        
        rules_dict = {}
        for base in bases:
            # We use the element_code (e.g., '7001', '6001') as the key
            code = base.element.element_code 
            rules_dict[code] = {
                'brackets': [
                    getattr(base, f'bracket_{i:02}') or Decimal(0) for i in range(16)
                ],
                'rates': [
                    getattr(base, f'rate_{i:02}') or Decimal(0) for i in range(16)
                ],
            }
        return rules_dict

    def calculate_progressive_tax(self, base_amount: Decimal, rule_code: str) -> Decimal:
        """
        Calculates tax based on the matrix brackets defined in Regulations.
        """
        if rule_code not in self.rules:
            # Log warning in production: Rule code not found in CalculationBase
            return Decimal('0.00')

        rule = self.rules[rule_code]
        brackets = rule['brackets']
        rates = rule['rates']
        
        tax = Decimal('0.00')
        previous_limit = Decimal('0.00')

        for i in range(16):
            limit = brackets[i]
            rate = rates[i]

            if limit == 0 and i > 0: 
                break # End of table

            # Calculate taxable amount in this bracket
            taxable_in_bracket = Decimal('0.00')
            
            if base_amount > previous_limit:
                # If limit is 0 (Infinity) or it's the last bracket
                if i == 15 or (limit == 0 and i == 0):
                    taxable_in_bracket = base_amount - previous_limit
                else:
                    taxable_in_bracket = min(base_amount, limit) - previous_limit

                if taxable_in_bracket > 0:
                    tax += taxable_in_bracket * (rate / 100)

            previous_limit = limit
            
            # If we haven't reached the limit of this bracket (and it's not infinity), stop
            if limit > 0 and base_amount <= limit:
                break
                
        return tax

    def get_valid_components(self, employee):
        """
        VALIDATION LOGIC:
        Filters payments acceptable for this payroll period.
        """
        period_start = self.period.start_date
        period_end = self.period.end_date

        # Base Query: Must be Active and NOT yet processed
        base_query = CompensationComponent.objects.filter(
            employee=employee,
            is_active=True,
            processed=False 
        ).select_related('pd_code')

        # 1. PERMANENT PAYMENTS (Category = Permanent)
        # Logic: Must overlap with the period dates
        permanent_query = Q(
            category=CompensationComponent.CATEGORY_PERMANENT,
            start_date__lte=period_end
        ) & (
            Q(end_date__isnull=True) | Q(end_date__gte=period_start)
        )

        # 2. VARIABLE / ONE-OFF PAYMENTS (Category = Variable)
        # Logic: Date must fall strictly within the period
        variable_query = Q(
            category=CompensationComponent.CATEGORY_VARIABLE,
            start_date__gte=period_start,
            start_date__lte=period_end
        )

        # 3. PRIOR DATES (Retroactive / Unprocessed)
        # Logic: Start Date < Period Start AND Not Processed
        retro_query = Q(
            start_date__lt=period_start,
            processed=False
        )

        # Combine logic
        final_query = base_query.filter(
            permanent_query | variable_query | retro_query
        )
        
        return final_query

    def calculate_bases(self, employee) -> Dict[str, Any]:
        """
        Aggregates valid components into Bases.
        Returns amount totals AND a breakdown of specific PD Codes for the report.
        """
        components = self.get_valid_components(employee)

        bases = {
            'TOTAL_GROSS': Decimal('0.00'),
            'BASE_6000': Decimal('0.00'),   # Taxable Base
            'BASE_7000': Decimal('0.00'),   # SS Base
            'breakdown': {} # To store { 'BASIC': 5000, 'BONUS': 1000 } for the GtN Report
        }

        for comp in components:
            pd = comp.pd_code
            
            # Check if Earning (Category Payment or Type EARNING)
            # Safe access to pdcode_type in case it's None
            pd_type = (pd.pdcode_type or '').upper()
            is_earning = pd.pdcode_category == 'Payment' or pd_type == 'EARNING'
            
            if is_earning:
                # Use simple amount, unless you have implemented get_period_amount on the model
                amount = comp.amount
                
                # Update Totals
                bases['TOTAL_GROSS'] += amount
                if pd.pdcode_taxable: bases['BASE_6000'] += amount
                if pd.pdcode_social_securitable: bases['BASE_7000'] += amount

                # Store for Report (Group by PD Code)
                code_key = pd.pdcode_code # e.g. "1001"
                bases['breakdown'][code_key] = bases['breakdown'].get(code_key, Decimal(0)) + amount

        return bases

    def calculate(self):
        results = []
        totals = {
            "gross": Decimal("0.00"),
            "inss": Decimal("0.00"),
            "irrf": Decimal("0.00"),
            "total_tax": Decimal("0.00"),
            "net": Decimal("0.00"),
        }
        
        for employee in self.employees:
            # 1. Calculate Bases & Get Breakdown
            bases_data = self.calculate_bases(employee)
            
            gross_pay = bases_data['TOTAL_GROSS']
            ss_base = bases_data['BASE_7000']
            tax_base_initial = bases_data['BASE_6000']
            
            # 2. Calculate Taxes
            inss_deduction = self.calculate_progressive_tax(ss_base, self.CODE_INSS_TABLE)
            
            adjusted_tax_base = tax_base_initial - inss_deduction
            if adjusted_tax_base < 0: adjusted_tax_base = Decimal('0.00')
            
            irrf_deduction = self.calculate_progressive_tax(adjusted_tax_base, self.CODE_IRRF_TABLE)

            total_tax = inss_deduction + irrf_deduction
            net_pay = gross_pay - total_tax

            # 3. Prepare Report Data (Merging Earnings Breakdown + Calculated Taxes)
            report_data = bases_data['breakdown'].copy() 
            report_data['INSS'] = inss_deduction         
            report_data['IRRF'] = irrf_deduction         

            results.append({
                "employee_id": employee.id,
                # FIXED: Use correct field names from your Employee model
                "employee_code": getattr(employee, 'employee_code', str(employee.id)),
                "employee_name": f"{employee.employee_name} {employee.employee_surname}",
                "department": getattr(employee, 'department', '-'),
                "gross": gross_pay,
                "total_tax": total_tax,
                "net": net_pay,
                # Store the FULL breakdown in JSON for the View to render the matrix
                "details": report_data 
            })

            # Update Totals
            totals["gross"] += gross_pay
            totals["inss"] += inss_deduction
            totals["irrf"] += irrf_deduction
            totals["total_tax"] += total_tax
            totals["net"] += net_pay

        return {"employee_results": results, "totals": totals}