from decimal import Decimal, ROUND_HALF_UP

class BasePayrollCalculator:
    """
    Base Payroll Calculator.
    Responsible for fetching INPUTS (Compensations) and registering them for the report.
    """
    
    def __init__(self, employee, period=None, **kwargs):
        self.employee = employee
        self.period = period
        
        # Output Storage
        self.breakdown = []    # List for the "Payslip" view
        self.results_dict = {} # Dict for the "Gross to Net" view
        self.log = []          # Logs

        # Totals
        self.taxable_gross = Decimal("0.00")
        self.non_taxable_gross = Decimal("0.00")
        self.total_gross = Decimal("0.00")

    def register(self, name, amount, code=None, description=None):
        """
        Registers a result with consistent parameter order.
        
        Args:
            name: Human-readable name for the item
            amount: Decimal amount
            code: Internal code for reporting (KEY for results_dict)
            description: Optional description
        """
        safe_amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        # 1. Add to List (for Breakdown/Payslip view)
        item = {
            "name": name, 
            "amount": safe_amount, 
            "description": description or name, 
            "code": code
        }
        self.breakdown.append(item)
        
        # 2. Add to Dict using CODE as key (for G2N Report)
        # This ensures the view can find elements by their code
        internal_key = code if code else name
        
        # Aggregate values if the same code is used multiple times
        if internal_key in self.results_dict:
            self.results_dict[internal_key] += safe_amount
        else:
            self.results_dict[internal_key] = safe_amount
            
        return safe_amount

def calculate(self):
        """Main execution method - fetches compensations and registers earnings."""
        # 1. Reset storage
        self.breakdown = []
        self.results_dict = {}
        self.taxable_gross = Decimal("0.00")
        self.non_taxable_gross = Decimal("0.00")
        self.total_gross = Decimal("0.00")
        
        # 2. SMART FETCH
        comps = None
        if hasattr(self.employee, 'compensationcomponent_set'):
            comps = self.employee.compensationcomponent_set
        elif hasattr(self.employee, 'compensations'):
            comps = self.employee.compensations
        elif hasattr(self.employee, 'components'):
            comps = self.employee.components
        elif hasattr(self.employee, 'compensation_components'): # Added based on your model related_name
            comps = self.employee.compensation_components
        
        # 3. Process Inputs
        if comps:
            # Filter active and date-valid components
            active_components = comps.filter(is_active=True)
            if self.period:
                # Add date filtering if period is available
                from django.db.models import Q
                active_components = active_components.filter(
                    Q(end_date__isnull=True) | Q(end_date__gte=self.period.start_date),
                    start_date__lte=self.period.end_date
                )
            
            for comp in active_components:
                # --- CORRECTION: USE PRORATION METHOD ---
                if self.period:
                    amt = comp.get_period_amount(self.period.start_date, self.period.end_date)
                else:
                    amt = comp.amount # Fallback
                
                amt = Decimal(str(amt))
                
                if amt != 0: 
                    # Determine Taxability
                    is_taxable = True
                    # Check Element first
                    if hasattr(comp, 'element') and comp.element:
                        is_taxable = getattr(comp.element, 'element_taxable', True)
                    
                    # Check PD Code second (override or fallback)
                    pd_obj = getattr(comp, 'pdcode', getattr(comp, 'pd_code', None))
                    if pd_obj:
                        if hasattr(pd_obj, 'pdcode_taxable'):
                            is_taxable = pd_obj.pdcode_taxable
                    
                    # Accumulate Totals
                    if is_taxable:
                        self.taxable_gross += amt
                    else:
                        self.non_taxable_gross += amt
                    self.total_gross += amt
                    
                    # Extract Name & Code
                    name = "Earnings"
                    code = None
                    
                    if pd_obj:
                        name = getattr(pd_obj, 'pdcode_description', name)
                        code = getattr(pd_obj, 'pdcode_code', None)
                    elif hasattr(comp, 'element') and comp.element:
                        name = comp.element.element_name
                        code = getattr(comp.element, 'element_code', None)

                    # REGISTER
                    self.register(
                        name=name, 
                        amount=amt, 
                        code=code if code else name,
                        description="Earnings"
                    )

        # 4. Register Totals
        self.results_dict['GROSS_PAYABLE'] = self.total_gross
        self.results_dict['TAXABLE_GROSS'] = self.taxable_gross

        return {
            "breakdown": self.breakdown,
            "elements": self.results_dict,
            "totals": {
                "gross": self.total_gross, 
                "taxable": self.taxable_gross,
                "net": self.total_gross 
            },
            "log": self.log
        }