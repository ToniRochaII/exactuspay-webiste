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
        
        # Active NI Code Default
        self.active_ni_code = "7001" 

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
        self.explicit_overrides = set() 
        self.active_ni_code = "7001"
        
        # 2. Aggregation
        self._aggregate_compensations()

        # 3. Collect UI info
        self._collect_pd_codes()
        
        # 4. Country Nuances
        self._apply_country_nuances()

        # 5. Standard Calculation Rules
        if self.period and self.period.payroll and CALCULATION_BASE_AVAILABLE:
            self._apply_calculation_rules()
        
        # --- CONSOLIDATION STEP ---
        self._consolidate_reporting_codes()
        # --------------------------
        
        # 6. Final Net Pay Calculation
        if '85000' in self.results_dict:
            self.results_dict['5000'] = self.results_dict['85000']
        elif '5999' in self.results_dict:
            self.results_dict['5000'] = self.results_dict['5999']

        gross_val = self.results_dict.get('5000', Decimal('0.00'))
        
        total_deductions = Decimal('0.00')
        
        # Iterate over a list copy to be safe
        for code, val in list(self.results_dict.items()):
            try:
                # 1. Skip if value is effectively zero
                if not val: continue
                
                # 2. Skip duplicates
                if code in self.salary_sacrifice_codes: continue
                if code in self.deduction_codes:
                    total_deductions += abs(val)
                    continue
                
                # 3. NET PAY PROTECTION
                # A. Skip Reporting Totals (6000, 7000, 9000)
                if code in ["6000", "7000", "9000"]: 
                    continue
                
                # B. [REMOVED] Skip Employer NI (7010) logic deleted.
                # Code 7010 IS NOW DEDUCTED.
                
                code_int = int(code)
                is_input_deduction = (2000 <= code_int <= 2999)
                is_tax_calc = (6001 <= code_int <= 6999)
                is_ni_calc  = (7001 <= code_int <= 7999)
                is_oth_calc = (9001 <= code_int <= 9999)

                if is_input_deduction or is_tax_calc or is_ni_calc or is_oth_calc:
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

    def _consolidate_reporting_codes(self):
        """
        Scans values for Tax/NI/Other and sums them into 6000/7000/9000.
        """
        total_tax = Decimal("0.00")
        total_ni = Decimal("0.00")
        total_other = Decimal("0.00")
        
        for code, val in list(self.results_dict.items()):
            try:
                code_int = int(code)
                if not val: continue

                # Tax Range (Exclude 6000)
                if 6001 <= code_int <= 6999:
                    total_tax += val/2
                
                # NI Range (Exclude 7000)
                elif 7001 <= code_int <= 7999:
                    # [STRICT] Code 7010 is INCLUDED here.
                    total_ni += val/2
                    
                # Other Range (Exclude 9000)
                elif 9001 <= code_int <= 9999:
                    total_other += val/2

            except (ValueError, TypeError):
                continue

        # --- FIX: FORCE INITIALIZATION ---
        # Ensure these keys exist in the dict, so _register_total picks them up even if 0.00
        for key in ["6000", "7000", "9000"]:
            if key not in self.results_dict:
                self.results_dict[key] = Decimal("0.00")

        # Register Totals
        self._register_total("6000", "PAYE Income Tax Total", total_tax)
        self._register_total("7000", "National Insurance Total", total_ni)
        self._register_total("9000", "Other Deductions Total", total_other)

    def _register_total(self, code, name, amount):
        if amount != 0 or code in self.results_dict:
            self.results_dict[code] = amount
            
            found_total = False
            for b in self.breakdown:
                if str(b.get('code')) == code:
                    b['amount'] = amount
                    found_total = True
                    break
            
            if not found_total and amount != 0:
                self.register(name, amount, code)

    def _apply_calculation_rules(self):
        regulation = self.period.payroll.regulation
        period_freq = self.period.frequency
        rules = CalculationBase.objects.filter(
            regulations=regulation,
            base_frequency=period_freq
        ).select_related('element', 'element_base')
        
        blocked_codes = {str(x).strip() for x in self.explicit_overrides}

        for rule in rules:
            try:
                if not rule.element: continue
                
                target_code = str(rule.element.element_code).strip()
                
                # --- REDIRECT LOGIC ---
                effective_code = target_code
                if target_code == "6000": effective_code = "6001"
                elif target_code == "7000": effective_code = self.active_ni_code
                elif target_code == "9000": effective_code = "9001"

                # 1. LOCK CHECK
                if effective_code in blocked_codes:
                    continue

                # 2. FAIL-SAFE
                current_val = self.results_dict.get(effective_code, Decimal("0.00"))
                if current_val != 0:
                    continue

                base_val = Decimal('0.00')
                if rule.element_base:
                    base_code = rule.element_base.element_code
                    base_val = self.results_dict.get(base_code, Decimal('0.00'))
                else:
                    # --- CONVENTION: Automatic Base Lookup for 9000 Series ---
                    # If no explicit base is defined for 9001-9999, look for 89001-89999
                    try:
                        tgt_int = int(target_code)
                        if 9001 <= tgt_int <= 9999:
                            auto_base = f"8{target_code}"
                            base_val = self.results_dict.get(auto_base, Decimal('0.00'))
                    except (ValueError, TypeError):
                        pass

                if base_val > 0:
                    calc_val = TaxEngine.calculate_progressive_tax(base_val, rule)
                    
                    if calc_val > 0:
                        try:
                            result_amt = -calc_val 
                            self.register(rule.element.element_name, result_amt, effective_code)
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
                    for base in ['86000', '86001']:
                        if base not in explicit_bases_found:
                            if is_deduction:
                                self.results_dict[base] = self.results_dict.get(base, Decimal('0.00')) - amt
                                self.results_dict[f'9{base[1:]}'] = self.results_dict.get(f'9{base[1:]}', Decimal('0.00')) - amt
                            else:
                                self.results_dict[base] = self.results_dict.get(base, Decimal('0.00')) + amt
                                self.results_dict[f'9{base[1:]}'] = self.results_dict.get(f'9{base[1:]}', Decimal('0.00')) + amt

                if getattr(pd, 'pdcode_social_securitable', False):
                    for base in ['87000', '87001']:
                        if base not in explicit_bases_found:
                            if is_deduction:
                                self.results_dict[base] = self.results_dict.get(base, Decimal('0.00')) - amt
                                self.results_dict[f'9{base[1:]}'] = self.results_dict.get(f'9{base[1:]}', Decimal('0.00')) - amt
                            else:
                                self.results_dict[base] = self.results_dict.get(base, Decimal('0.00')) + amt
                                self.results_dict[f'9{base[1:]}'] = self.results_dict.get(f'9{base[1:]}', Decimal('0.00')) + amt

    def _build_return(self, net_pay):
        return {
            'breakdown': self.breakdown,
            'elements': self.results_dict,
            'pd_codes': self.pd_codes,
            'totals': {'gross': self.results_dict.get('5000', 0), 'net': net_pay}
        }