from decimal import Decimal
from Exactus.payroll.calculator.base import BasePayrollCalculator
from Exactus.payroll.calculator.engine import TaxEngine
import logging

logger = logging.getLogger(__name__)

# --- IMPORT MODELS SAFELY ---
try:
    from Exactus.elements.models import Element
    ELEMENTS_AVAILABLE = True
except ImportError:
    Element = None
    ELEMENTS_AVAILABLE = False

try:
    from Exactus.calculationbase.models import CalculationBase
    CALCULATION_BASE_AVAILABLE = True
except ImportError:
    CalculationBase = None
    CALCULATION_BASE_AVAILABLE = False

class UniversalPayrollCalculator(BasePayrollCalculator):
    def __init__(self, employee, period, **kwargs):
        super().__init__(employee, period, **kwargs)
        if not hasattr(self, 'total_gross'): self.total_gross = Decimal("0.00")
        if not hasattr(self, 'taxable_gross'): self.taxable_gross = Decimal("0.00")
        if not hasattr(self, 'total_deductions'): self.total_deductions = Decimal("0.00")
        self.pd_codes = []

    def calculate(self):
        # 1. Init
        self.results_dict = {} 
        self.breakdown = []
        
        # 2. Aggregation
        self._aggregate_compensations()

        # 3. Collect UI info
        self._collect_pd_codes()
        
        # 4. Calculation Rules
        if self.period and self.period.payroll and CALCULATION_BASE_AVAILABLE:
            self._apply_calculation_rules()
        
        # 5. Final Net Pay Calculation
        
        # A. Ensure Gross Pay (5000) exists
        if '5000' not in self.results_dict and '5999' in self.results_dict:
            self.results_dict['5000'] = self.results_dict['5999']

        gross_val = self.results_dict.get('5000', Decimal('0.00'))
        
        # B. Calculate Total Deductions (Range 6000 - 7999)
        # We explicitly exclude 9000+ (Employer Costs) from this deduction sum
        total_deductions = Decimal('0.00')
        
        for code, val in self.results_dict.items():
            try:
                code_int = int(code)
                # STRICT RANGE CHECK: 6000 to 7999 inclusive (Employee Deductions)
                if 6000 <= code_int <= 7999:
                    total_deductions += abs(val)
            except (ValueError, TypeError):
                continue
            
        net_pay = gross_val - total_deductions
        
        # Store Net Pay as '8000'
        self.register("Net Salary", net_pay, "8000")

        return self._build_return(net_pay)

    def _aggregate_compensations(self):
        """Sum payments into Base Codes and store Earnings Codes."""
        comps = self._get_compensation_list()
        if not comps: return

        # Exclude items that are already processed (Paid)
        active_comps = comps.filter(is_active=True, processed=False)
        
        if self.period:
            from django.db.models import Q
            active_comps = active_comps.filter(
                Q(end_date__isnull=True) | Q(end_date__gte=self.period.start_date),
                start_date__lte=self.period.end_date
            ).select_related('pd_code')

        for comp in active_comps:
            if self.period: amt = comp.get_period_amount(self.period.start_date, self.period.end_date)
            else: amt = comp.amount
            amt = Decimal(str(amt))
            
            pd = getattr(comp, 'pdcode', getattr(comp, 'pd_code', None))
            
            if pd:
                # Store Earning Code
                if pd.pdcode_code:
                    self.results_dict[pd.pdcode_code] = self.results_dict.get(pd.pdcode_code, Decimal('0.00')) + amt

                # Sum into Bases
                bases_found = False
                if hasattr(pd, 'applicable_bases'):
                    for base in pd.applicable_bases.all():
                        bases_found = True
                        code = base.element_code
                        self.results_dict[code] = self.results_dict.get(code, Decimal('0.00')) + amt
                
                # Fallback Flags
                if not bases_found:
                    if getattr(pd, 'pdcode_payable', False):
                        self.results_dict['5999'] = self.results_dict.get('5999', Decimal('0.00')) + amt
                    if getattr(pd, 'pdcode_taxable', False):
                        self.results_dict['5600'] = self.results_dict.get('5600', Decimal('0.00')) + amt
                    if getattr(pd, 'pdcode_social_securitable', False):
                        self.results_dict['5700'] = self.results_dict.get('5700', Decimal('0.00')) + amt

    def _apply_calculation_rules(self):
        regulation = self.period.payroll.regulation
        rules = CalculationBase.objects.filter(regulations=regulation).select_related('element', 'element_base')
        
        for rule in rules:
            try:
                base_val = Decimal('0.00')
                if rule.element_base:
                    base_code = rule.element_base.element_code
                    base_val = self.results_dict.get(base_code, Decimal('0.00'))
                
                if base_val > 0:
                    calc_val = TaxEngine.calculate_progressive_tax(base_val, rule)
                    target = rule.element
                    
                    if calc_val > 0:
                        # [FIX] Determine Sign based on Code Range
                        # 5000 = Gross (Positive)
                        # 9000+ = Employer Contributions (Positive Cost)
                        # Others = Deductions (Negative)
                        
                        try:
                            code_int = int(target.element_code)
                            if code_int == 5000 or code_int >= 9000:
                                result_amt = calc_val
                            else:
                                result_amt = -calc_val
                        except (ValueError, TypeError):
                            # Default to deduction if code is weird
                            result_amt = -calc_val

                        # Register
                        self.register(target.element_name, result_amt, target.element_code)
            except Exception as e:
                logger.error(f"Error calculating rule {rule}: {e}")

    def _get_compensation_list(self):
        for attr in ['compensationcomponent_set', 'compensations', 'components', 'compensation_components']:
            if hasattr(self.employee, attr): return getattr(self.employee, attr)
        return None

    def _collect_pd_codes(self):
        comps = self._get_compensation_list()
        if comps:
            for c in comps.filter(is_active=True, processed=False):
                pd = getattr(c, 'pdcode', getattr(c, 'pd_code', None))
                if pd:
                    self.pd_codes.append({
                        'code': getattr(pd, 'pdcode_code', ''),
                        'description': getattr(pd, 'pdcode_description', ''),
                        'amount': c.amount
                    })

    def _build_return(self, net_pay):
        return {
            'breakdown': self.breakdown,
            'elements': self.results_dict,
            'pd_codes': self.pd_codes,
            'totals': {'gross': self.results_dict.get('5000', 0), 'net': net_pay}
        }