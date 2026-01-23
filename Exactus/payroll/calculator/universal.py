import importlib
from decimal import Decimal
from django.db.models import Q
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
        # Initialize standard totals
        self.total_gross = Decimal("0.00")
        self.taxable_gross = Decimal("0.00")
        self.total_deductions = Decimal("0.00")
        
        # Containers for UI and logic
        self.pd_codes = []
        self.deduction_codes = set()
        self.salary_sacrifice_codes = set()

        # Determine Country Slug for Strategy Loading
        self.country_slug = ""
        if self.period and self.period.payroll and self.period.payroll.country:
            self.country_slug = self.period.payroll.country.slug.lower().replace("-", "_")

    def calculate(self):
        # 1. Init Results Dictionary
        self.results_dict = {} 
        self.breakdown = []
        
        # 2. Aggregation (Populates 8xxxx and 9xxxx bases from inputs)
        self._aggregate_compensations()

        # 3. Collect UI info (For the payslip display)
        self._collect_pd_codes()
        
        # 4. Standard Calculation Rules (Database Driven - Taxes, etc.)
        if self.period and self.period.payroll and CALCULATION_BASE_AVAILABLE:
            self._apply_calculation_rules()

        # 5. Country Specific Nuances (Dynamic Strategy)
        self._apply_country_nuances()
        
        # 6. Final Net Pay Calculation
        
        # A. Ensure Gross Pay (5000) matches the Periodic Gross Base (85000)
        if '85000' in self.results_dict:
            self.results_dict['5000'] = self.results_dict['85000']
        elif '5999' in self.results_dict:
            # Fallback for legacy setups
            self.results_dict['5000'] = self.results_dict['5999']

        gross_val = self.results_dict.get('5000', Decimal('0.00'))
        
        # B. Calculate Total Deductions
        total_deductions = Decimal('0.00')
        
        for code, val in self.results_dict.items():
            try:
                # SKIP Salary Sacrifice (already reduced Gross Base 85000)
                if code in self.salary_sacrifice_codes:
                    continue

                # Add explicit deductions (marked during aggregation)
                if code in self.deduction_codes:
                    total_deductions += abs(val)
                    continue

                # Range-based checks for deductions (standard convention)
                # 2000-2999: Input Deductions
                # 6000-7999: Calculated Deductions (Taxes)
                code_int = int(code)
                is_input_deduction = (2000 <= code_int <= 2999)
                is_calc_deduction = (6000 <= code_int <= 7999)

                if is_input_deduction or is_calc_deduction:
                    total_deductions += abs(val)

            except (ValueError, TypeError):
                continue
            
        net_pay = gross_val - total_deductions
        
        # Store Net Pay (8000)
        self.register("Net Salary", net_pay, "8000")
        
        # Register Net Pay Bases (88000/98000)
        self.results_dict['88000'] = net_pay
        self.results_dict['98000'] = net_pay 

        return self._build_return(net_pay)

    def _aggregate_compensations(self):
        """
        Sum payments into Base Codes (8xxxx/9xxxx) and store Earnings Codes.
        """
        comps = self._get_compensation_list()
        if not comps: return

        active_comps = comps.filter(is_active=True, processed=False)
        
        if self.period:
            # Filter by date range
            active_comps = active_comps.filter(
                start_date__lte=self.period.end_date
            ).select_related('pd_code')

            # Additional Run Logic (Variable only)
            if getattr(self.period, 'is_additional', False):
                active_comps = active_comps.filter(
                    Q(category='VARIABLE') | Q(frequency='one_time')
                )

        for comp in active_comps:
            # --- Amount Calculation (Proration) ---
            if self.period:
                if comp.start_date > self.period.end_date:
                    continue 
                is_ended_in_past = comp.end_date and comp.end_date < self.period.start_date
                
                if is_ended_in_past:
                    if comp.category == 'PERMANENT': continue 
                    else: amt = comp.amount
                else:
                    amt = comp.get_period_amount(self.period.start_date, self.period.end_date)
            else: 
                amt = comp.amount
            
            amt = Decimal(str(amt))
            pd = getattr(comp, 'pdcode', getattr(comp, 'pd_code', None))
            
            if pd and pd.pdcode_code:
                code = pd.pdcode_code
                cat = getattr(pd, 'category', getattr(pd, 'pdcode_category', ''))
                is_deduction = str(cat).upper() == 'DEDUCTION'

                # 1. Store the value on the code itself (e.g., 1000)
                if is_deduction:
                    self.results_dict[code] = self.results_dict.get(code, Decimal('0.00')) + amt
                    self.deduction_codes.add(code)
                else:
                    self.results_dict[code] = self.results_dict.get(code, Decimal('0.00')) + amt

                # --- 2. AUTOMATIC BASE MAPPING (8xxxx / 9xxxx) ---
                # Rule: Code X sums into 8X (Period) and 9X (YTD)
                try:
                    int(code) # Ensure numeric
                    p_base = f"8{code}" # Period Base
                    y_base = f"9{code}" # YTD Base
                    
                    # Add to bases (Always positive accumulation for tracking)
                    self.results_dict[p_base] = self.results_dict.get(p_base, Decimal('0.00')) + amt
                    self.results_dict[y_base] = self.results_dict.get(y_base, Decimal('0.00')) + amt
                except ValueError:
                    pass 

                # --- 3. EXPLICIT BASES (Database Links) ---
                # Check if this element is linked to other specific bases in the DB
                explicit_bases_found = set()
                if hasattr(pd, 'applicable_bases'):
                    for base in pd.applicable_bases.all():
                        b_code = base.element_code
                        explicit_bases_found.add(b_code)
                        
                        if is_deduction:
                            self.results_dict[b_code] = self.results_dict.get(b_code, Decimal('0.00')) - amt
                            # Salary Sacrifice Check (Reduces Gross Base 85000)
                            if b_code == '85000':
                                self.salary_sacrifice_codes.add(code)
                        else:
                            self.results_dict[b_code] = self.results_dict.get(b_code, Decimal('0.00')) + amt

                # --- 4. STANDARD FLAGS (General Accumulators) ---
                # Maps standard boolean flags to 85000/86000/87000.
                # Only applies if NOT explicitly overridden in step 3.
                
                # A. PAYABLE (Gross Pay) -> 85000 / 95000
                if getattr(pd, 'pdcode_payable', False) and not is_deduction:
                    if '85000' not in explicit_bases_found:
                        self.results_dict['85000'] = self.results_dict.get('85000', Decimal('0.00')) + amt
                        self.results_dict['95000'] = self.results_dict.get('95000', Decimal('0.00')) + amt
                
                # B. TAXABLE -> 86000 / 96000
                if getattr(pd, 'pdcode_taxable', False):
                    if '86000' not in explicit_bases_found:
                        if is_deduction:
                            self.results_dict['86000'] = self.results_dict.get('86000', Decimal('0.00')) - amt
                            self.results_dict['96000'] = self.results_dict.get('96000', Decimal('0.00')) - amt
                        else:
                            self.results_dict['86000'] = self.results_dict.get('86000', Decimal('0.00')) + amt
                            self.results_dict['96000'] = self.results_dict.get('96000', Decimal('0.00')) + amt

                # C. SOCIAL SECURITY -> 87000 / 97000
                if getattr(pd, 'pdcode_social_securitable', False):
                    if '87000' not in explicit_bases_found:
                        if is_deduction:
                            self.results_dict['87000'] = self.results_dict.get('87000', Decimal('0.00')) - amt
                            self.results_dict['97000'] = self.results_dict.get('97000', Decimal('0.00')) - amt
                        else:
                            self.results_dict['87000'] = self.results_dict.get('87000', Decimal('0.00')) + amt
                            self.results_dict['97000'] = self.results_dict.get('97000', Decimal('0.00')) + amt

    def _apply_calculation_rules(self):
        """
        Apply database-defined calculation rules (CalculationBase).
        """
        regulation = self.period.payroll.regulation
        period_freq = self.period.frequency  # Get current period frequency

        # --- UPDATED: Filter by Regulations AND Frequency ---
        rules = CalculationBase.objects.filter(
            regulations=regulation,
            base_frequency=period_freq  # STRICT LINKING
        ).select_related('element', 'element_base')
        
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
                        try:
                            code_int = int(target.element_code)
                            
                            # Logic: Deductions are negative, Employer Costs (9xxx) are positive
                            if code_int == 5000 or code_int >= 9000:
                                result_amt = calc_val 
                            else:
                                result_amt = -calc_val 
                                
                            self.register(target.element_name, result_amt, target.element_code)
                            
                        except (ValueError, TypeError):
                            pass
                            
            except Exception as e:
                logger.error(f"Error calculating rule {rule}: {e}")

    def _apply_country_nuances(self):
        """
        Dynamically imports a country specific calculator logic.
        Looks for: Exactus.payroll.calculator.countries.{slug}.calculator
        """
        if not self.country_slug:
            return

        module_path = f"Exactus.payroll.calculator.countries.{self.country_slug}.calculator"
        
        try:
            module = importlib.import_module(module_path)
            
            strategy_class = None
            clean_name = self.country_slug.replace("_", "").lower()
            
            for attr in dir(module):
                # Search for a class like 'BrazilPayrollStrategy'
                if attr.lower().endswith("payrollstrategy"):
                    if clean_name in attr.lower():
                        strategy_class = getattr(module, attr)
                        break
            
            if strategy_class:
                # Instantiate and Run Strategy
                strategy = strategy_class(self)
                strategy.process_nuances()
                logger.info(f"Applied country strategy from {module_path}")
            else:
                logger.debug(f"Module {module_path} found, but no matching strategy class found.")

        except ImportError:
            # Expected if no specific country file exists
            pass
        except Exception as e:
            logger.error(f"Error applying country strategy for {self.country_slug}: {e}")

    def _get_compensation_list(self):
        for attr in ['compensationcomponent_set', 'compensations', 'components', 'compensation_components']:
            if hasattr(self.employee, attr): return getattr(self.employee, attr)
        return None

    def _collect_pd_codes(self):
        comps = self._get_compensation_list()
        if comps:
            active_comps = comps.filter(is_active=True, processed=False)
            
            if self.period and getattr(self.period, 'is_additional', False):
                active_comps = active_comps.filter(
                    Q(category='VARIABLE') | Q(frequency='one_time')
                )

            for c in active_comps:
                amount_to_show = Decimal('0.00')
                should_show = True
                if self.period:
                    if c.start_date > self.period.end_date:
                        should_show = False
                    elif c.end_date and c.end_date < self.period.start_date:
                        if c.category == 'PERMANENT':
                            should_show = False
                        else:
                            amount_to_show = c.amount
                    else:
                        amount_to_show = c.get_period_amount(self.period.start_date, self.period.end_date)
                else:
                    amount_to_show = c.amount
                
                if should_show:
                    pd = getattr(c, 'pdcode', getattr(c, 'pd_code', None))
                    if pd:
                        self.pd_codes.append({
                            'code': getattr(pd, 'pdcode_code', ''),
                            'description': getattr(pd, 'pdcode_description', ''),
                            'amount': amount_to_show
                        })

    def _build_return(self, net_pay):
        return {
            'breakdown': self.breakdown,
            'elements': self.results_dict,
            'pd_codes': self.pd_codes,
            'totals': {'gross': self.results_dict.get('5000', 0), 'net': net_pay}
        }