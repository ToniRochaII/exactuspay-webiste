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
        
        self.total_gross = Decimal("0.00")
        self.taxable_gross = Decimal("0.00")
        self.total_deductions = Decimal("0.00")
        
        self.pd_codes = []
        self.deduction_codes = set()
        self.salary_sacrifice_codes = set()
        
        # Override Container
        self.explicit_overrides = set()

        self.country_slug = ""
        if self.period and self.period.payroll and self.period.payroll.country:
            raw_slug = self.period.payroll.country.slug.lower()
            if raw_slug == "united-kingdom":
                self.country_slug = "gb"
            else:
                self.country_slug = raw_slug.replace("-", "_")

    def calculate(self):
        self.results_dict = {} 
        self.breakdown = []
        # Reset overrides at start
        self.explicit_overrides = set() 
        
        # 2. Aggregation
        self._aggregate_compensations()

        # 3. Collect UI info
        self._collect_pd_codes()
        
        # 4. Country Nuances (Runs calculator.py logic - Calculates 0T here)
        self._apply_country_nuances()

        # 5. Standard Calculation Rules (Runs DB Engine)
        if self.period and self.period.payroll and CALCULATION_BASE_AVAILABLE:
            self._apply_calculation_rules()
        
        # --- CONSOLIDATION STEP ---
        # Sums 6001-6998 into 6000 (Reporting Only)
        self._consolidate_tax_codes()
        # --------------------------
        
        # 6. Final Net Pay Calculation
        if '85000' in self.results_dict:
            self.results_dict['5000'] = self.results_dict['85000']
        elif '5999' in self.results_dict:
            self.results_dict['5000'] = self.results_dict['5999']

        gross_val = self.results_dict.get('5000', Decimal('0.00'))
        
        total_deductions = Decimal('0.00')
        for code, val in self.results_dict.items():
            try:
                # Skip duplicate deductions logic
                if code in self.salary_sacrifice_codes: continue
                if code in self.deduction_codes:
                    total_deductions += abs(val)
                    continue
                
                # --- NET PAY PROTECTION ---
                # Code 6000 is just a "Total" reporting line. 
                # We skip it here because we are already deducting the individual 
                # lines (6001, 6100, etc.) below.
                if code == "6000": 
                    continue
                # --------------------------

                code_int = int(code)
                is_input_deduction = (2000 <= code_int <= 2999)
                is_calc_deduction = (6001 <= code_int <= 7999)

                if is_input_deduction or is_calc_deduction:
                    total_deductions += abs(val)
            except (ValueError, TypeError):
                continue
            
        net_pay = gross_val - total_deductions
        
        self.results_dict['8000'] = Decimal("0.00")
        self.results_dict['88000'] = Decimal("0.00")
        self.results_dict['98000'] = Decimal("0.00")

        self.register("Net Salary", net_pay, "8000")
        self.results_dict['88000'] = net_pay
        self.results_dict['98000'] = net_pay 

        return self._build_return(net_pay)

    def _consolidate_tax_codes(self):
        """
        Scans tax values (6001-6998).
        Sums them into 6000 for reporting purposes.
        Does NOT remove the individual lines from results_dict.
        """
        total_tax = Decimal("0.00")
        
        # 1. Sum up values
        for code, val in self.results_dict.items():
            try:
                code_int = int(code)
                # Check range 6001 to 6998
                if 6001 <= code_int <= 6998:
                    if val != 0:
                        total_tax += val/2
            except (ValueError, TypeError):
                continue

        # 2. Store the Total in 6000 (Reporting Only)
        if total_tax != 0:
            self.results_dict["6000"] = total_tax
            
            # Update or Add the 6000 Total line in Breakdown
            found_total = False
            for b in self.breakdown:
                if str(b.get('code')) == "6000":
                    b['amount'] = total_tax
                    found_total = True
                    break
            
            if not found_total:
                self.register("PAYE Income Tax Total", total_tax, "6000")

    def _aggregate_compensations(self):
        comps = self._get_compensation_list()
        if not comps: return

        active_comps = comps.filter(is_active=True, processed=False)
        if self.period:
            active_comps = active_comps.filter(start_date__lte=self.period.end_date).select_related('pd_code')
            if getattr(self.period, 'is_additional', False):
                active_comps = active_comps.filter(Q(category='VARIABLE') | Q(frequency='one_time'))

        for comp in active_comps:
            if self.period:
                if comp.start_date > self.period.end_date: continue 
                is_ended_in_past = comp.end_date and comp.end_date < self.period.start_date
                if is_ended_in_past:
                    if comp.category == 'PERMANENT': continue 
                    else: amt = comp.amount
                else: amt = comp.get_period_amount(self.period.start_date, self.period.end_date)
            else: amt = comp.amount
            
            amt = Decimal(str(amt))
            pd = getattr(comp, 'pdcode', getattr(comp, 'pd_code', None))
            
            if pd and pd.pdcode_code:
                code = pd.pdcode_code
                cat = getattr(pd, 'category', getattr(pd, 'pdcode_category', ''))
                is_deduction = str(cat).upper() == 'DEDUCTION'

                if is_deduction:
                    self.results_dict[code] = self.results_dict.get(code, Decimal('0.00')) + amt
                    self.deduction_codes.add(code)
                else:
                    self.results_dict[code] = self.results_dict.get(code, Decimal('0.00')) + amt

                try:
                    int(code)
                    p_base = f"8{code}"
                    y_base = f"9{code}"
                    self.results_dict[p_base] = self.results_dict.get(p_base, Decimal('0.00')) + amt
                    self.results_dict[y_base] = self.results_dict.get(y_base, Decimal('0.00')) + amt
                except ValueError: pass 

                explicit_bases_found = set()
                if hasattr(pd, 'applicable_bases'):
                    for base in pd.applicable_bases.all():
                        b_code = base.element_code
                        explicit_bases_found.add(b_code)
                        if is_deduction:
                            self.results_dict[b_code] = self.results_dict.get(b_code, Decimal('0.00')) - amt
                            if b_code == '85000': self.salary_sacrifice_codes.add(code)
                        else:
                            self.results_dict[b_code] = self.results_dict.get(b_code, Decimal('0.00')) + amt

                if getattr(pd, 'pdcode_payable', False) and not is_deduction:
                    if '85000' not in explicit_bases_found:
                        self.results_dict['85000'] = self.results_dict.get('85000', Decimal('0.00')) + amt
                        self.results_dict['95000'] = self.results_dict.get('95000', Decimal('0.00')) + amt
                
                if getattr(pd, 'pdcode_taxable', False):
                    if '86001' not in explicit_bases_found:
                        if is_deduction:
                            self.results_dict['86001'] = self.results_dict.get('86001', Decimal('0.00')) - amt
                            self.results_dict['96001'] = self.results_dict.get('96001', Decimal('0.00')) - amt
                        else:
                            self.results_dict['86001'] = self.results_dict.get('86001', Decimal('0.00')) + amt
                            self.results_dict['96001'] = self.results_dict.get('96001', Decimal('0.00')) + amt

                if getattr(pd, 'pdcode_social_securitable', False):
                    if '87000' not in explicit_bases_found:
                        if is_deduction:
                            self.results_dict['87000'] = self.results_dict.get('87000', Decimal('0.00')) - amt
                            self.results_dict['97000'] = self.results_dict.get('97000', Decimal('0.00')) - amt
                        else:
                            self.results_dict['87000'] = self.results_dict.get('87000', Decimal('0.00')) + amt
                            self.results_dict['97000'] = self.results_dict.get('97000', Decimal('0.00')) + amt

    def _apply_calculation_rules(self):
        regulation = self.period.payroll.regulation
        period_freq = self.period.frequency
        rules = CalculationBase.objects.filter(
            regulations=regulation,
            base_frequency=period_freq
        ).select_related('element', 'element_base')
        
        # --- STRICT LOCK LOGIC (Prevents Double Calculation) ---
        blocked_codes = {str(x).strip() for x in self.explicit_overrides}

        for rule in rules:
            try:
                if not rule.element: continue
                
                target_code = str(rule.element.element_code).strip()
                
                # 1. PRIMARY LOCK: Check if this code is in the block list
                if target_code in blocked_codes:
                    continue

                # 2. FAIL-SAFE LOCK: Check if Tax is ALREADY calculated (e.g. by 0T manual logic)
                # If '6001' is already populated with a non-zero value, DO NOT run the DB rule.
                if target_code == "6001" and self.results_dict.get("6001", Decimal("0.00")) != 0:
                     continue

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
                            if code_int == 5000 or code_int >= 9000: result_amt = calc_val 
                            else: result_amt = -calc_val 
                            self.register(target.element_name, result_amt, target.element_code)
                        except (ValueError, TypeError): pass
            except Exception as e:
                logger.error(f"Error calculating rule {rule}: {e}")

    def _apply_country_nuances(self):
        if not self.country_slug: return
        module_path = f"Exactus.payroll.calculator.countries.{self.country_slug}.calculator"
        try:
            module = importlib.import_module(module_path)
            strategy_class = None
            for attr in dir(module):
                if attr.lower().endswith("payrollstrategy") and attr != "BasePayrollStrategy":
                    strategy_class = getattr(module, attr)
                    break
            if strategy_class:
                strategy = strategy_class(self)
                strategy.process_nuances()
                logger.info(f"Applied country strategy from {module_path}")
        except ImportError: pass
        except Exception as e: logger.error(f"Error applying country strategy for {self.country_slug}: {e}")

    def _get_compensation_list(self):
        for attr in ['compensationcomponent_set', 'compensations', 'components', 'compensation_components']:
            if hasattr(self.employee, attr): return getattr(self.employee, attr)
        return None

    def _collect_pd_codes(self):
        comps = self._get_compensation_list()
        if comps:
            active_comps = comps.filter(is_active=True, processed=False)
            if self.period and getattr(self.period, 'is_additional', False):
                active_comps = active_comps.filter(Q(category='VARIABLE') | Q(frequency='one_time'))
            for c in active_comps:
                amount_to_show = Decimal('0.00')
                should_show = True
                if self.period:
                    if c.start_date > self.period.end_date: should_show = False
                    elif c.end_date and c.end_date < self.period.start_date:
                        if c.category == 'PERMANENT': should_show = False
                        else: amount_to_show = c.amount
                    else: amount_to_show = c.get_period_amount(self.period.start_date, self.period.end_date)
                else: amount_to_show = c.amount
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