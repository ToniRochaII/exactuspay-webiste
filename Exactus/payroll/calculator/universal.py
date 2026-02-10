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
            
            # --- GROSS PAY CALCULATION ---
            self._calculate_gross_pay()

            # --- CONSOLIDATION STEP ---
            # This populates 6000 and 7000 (divided by 2 as requested)
            self._consolidate_reporting_codes()
            
            # --- 6. FINAL NET PAY CALCULATION (USER FORMULA) ---
            # Formula: Net = 5000 - 6000 - 7000 - (6400-6999) - (7400-7999)
            
            # A. Get Base Values
            gross_val = self.results_dict.get('5000', Decimal('0.00'))
            tax_total = self.results_dict.get('6000', Decimal('0.00')) # This is the /2 value
            ni_total  = self.results_dict.get('7000', Decimal('0.00')) # This is the /2 value
            
            # B. Calculate "Others" (Ranges 6400-6999 and 7400-7999)
            other_deductions = Decimal('0.00')
            
            for code, val in self.results_dict.items():
                try:
                    if not val: continue
                    code_int = int(code)
                    
                    # Check User-Defined Deduction Ranges
                    in_tax_other_range = (6400 <= code_int <= 6999)
                    in_ni_other_range  = (7400 <= code_int <= 7999)
                    
                    if in_tax_other_range or in_ni_other_range:
                        other_deductions += abs(val)

                except (ValueError, TypeError):
                    continue
                
            # C. Apply Formula
            # We use abs() to ensure we subtract the magnitude, regardless of how the sign is stored.
            # Net = Gross - Tax(6000) - NI(7000) - Others
            net_pay = gross_val - abs(tax_total) - abs(ni_total) - abs(other_deductions)
            
            # D. Store Result
            self.results_dict['8000'] = Decimal("0.00")
            self.results_dict['88000'] = Decimal("0.00")
            self.results_dict['98000'] = Decimal("0.00")

            self.register("Net Salary", net_pay, "8000")
            self.results_dict['88000'] = net_pay
            self.results_dict['98000'] = net_pay 

            return self._build_return(net_pay)

    def _calculate_gross_pay(self):
        """
        Calculates Gross Pay (5000) based on specific ranges:
        + (1000 - 1999) : Basic Payments
        - (2000 - 2999) : Input Deductions
        + (3000 - 4999) : Other Payments
        """
        gross_sum = Decimal('0.00')

        for code, val in self.results_dict.items():
            try:
                if not val: continue
                code_int = int(code)

                # Range 1: 1000 - 1999 (Add)
                if 1000 <= code_int <= 1999:
                    gross_sum += val
                
                # Range 2: 2000 - 2999 (Subtract)
                elif 2000 <= code_int <= 2999:
                    gross_sum -= abs(val) # Ensure we subtract absolute value
                
                # Range 3: 3000 - 4999 (Add)
                elif 3000 <= code_int <= 4999:
                    gross_sum += val

            except (ValueError, TypeError):
                continue

        # Register the calculated Gross
        self.results_dict['5000'] = gross_sum
        
        # Ensure legacy tax base (86000) matches if not explicitly set by overrides
        if '86000' not in self.results_dict or self.results_dict['86000'] == 0:
            self.results_dict['86000'] = gross_sum


    def _consolidate_reporting_codes(self):
        """
        FIXED: VLOOKUP STYLE CONSOLIDATION WITH /2 ADJUSTMENT FOR ALL
        Picks the specific tax/NI code based on Employee Settings, ignoring duplicates.
        """
        # --- 1. GET EMPLOYEE DATA ---
        raw_tax_code = getattr(self.employee, 'tax_info_03', 'BR') or 'BR'
        clean_tax_code = raw_tax_code.upper().strip()
        
        # Remove Country Prefixes for clean mapping
        if self.country_slug == 'gb' and (clean_tax_code.startswith('S') or clean_tax_code.startswith('C')):
             clean_tax_code = clean_tax_code[1:]

        ni_category = getattr(self.employee, 'tax_info_05', 'A') or 'A'

        # --- 2. MAP TO TARGET CODES (VLOOKUP) ---
        
        # Tax Mapping
        target_tax_code = "6001" # Default (Standard)
        if clean_tax_code.startswith("BR"):
            target_tax_code = "6100"
        elif clean_tax_code.startswith("D0"):
            target_tax_code = "6200"
        elif clean_tax_code.startswith("D1"):
            target_tax_code = "6300"

        # NI Mapping
        ni_map = {
            "A": "7001", "B": "7010", "C": "7020", 
            "H": "7030", "J": "7040", "M": "7050", "Z": "7060"
        }
        target_ni_code = ni_map.get(ni_category.upper(), "7001")

        # --- 3. FETCH SINGLE CORRECT VALUE ---
        total_tax = self.results_dict.get(target_tax_code, Decimal("0.00"))
        total_ni = self.results_dict.get(target_ni_code, Decimal("0.00"))

        # --- 4. FETCH OTHER (Sum Range for Employer Costs) ---
        total_other = Decimal("0.00")
        for code, val in self.results_dict.items():
            if not val: continue
            try:
                c_int = int(code)
                if 9001 <= c_int <= 9399:
                    total_other += val
            except (ValueError, TypeError):
                continue

        # --- 5. REGISTER TOTALS ---
        for key in ["6000", "7000", "9000"]:
            if key not in self.results_dict:
                self.results_dict[key] = Decimal("0.00")

        # [REQUESTED CHANGE] Divide ALL Reporting Totals by 2
        self._register_total("6000", "PAYE Income Tax Total", total_tax / 2)
        self._register_total("7000", "National Insurance Total", total_ni / 2)
        
        # Note: -total_other flips it to a cost, then we divide by 2
        self._register_total("9000", "Other Deductions Total", (-total_other) / 2)

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
                
                effective_code = target_code
                if target_code == "6000": effective_code = "6001"
                elif target_code == "7000": effective_code = self.active_ni_code
                elif target_code == "9000": effective_code = "9001"

                if effective_code in blocked_codes:
                    continue

                current_val = self.results_dict.get(effective_code, Decimal("0.00"))
                if current_val != 0:
                    continue

                base_val = Decimal('0.00')
                if rule.element_base:
                    base_code = rule.element_base.element_code
                    base_val = self.results_dict.get(base_code, Decimal('0.00'))
                else:
                    try:
                        tgt_int = int(target_code)
                        if 9001 <= tgt_int <= 9399:
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
        if not self.country_slug: 
            print("❌ [Universal] No Country Slug found!")
            return

        module_path = f"Exactus.payroll.calculator.countries.{self.country_slug}.calculator"
        print(f"--- 🌍 ATTEMPTING TO LOAD: {module_path} ---")

        try:
            module = importlib.import_module(module_path)
            strategy_class = None
            for attr in dir(module):
                if attr.lower().endswith("payrollstrategy") and attr != "BasePayrollStrategy":
                    strategy_class = getattr(module, attr)
                    break
            
            if strategy_class:
                print(f"   ✅ FOUND STRATEGY: {strategy_class.__name__}")
                strategy = strategy_class(self)
                strategy.process_nuances()
                print(f"   🚀 EXECUTED STRATEGY SUCCESSFULLY")
            else:
                print(f"   ❌ NO STRATEGY CLASS FOUND IN {module_path}")

        except ImportError as e:
            print(f"   🔥 IMPORT ERROR: Could not load {module_path}")
            print(f"   🔥 REASON: {e}")
            # Do NOT pass. Let it print so we see it in the logs.
        except Exception as e:
            print(f"   🔥 GENERAL ERROR loading strategy: {e}")
            import traceback
            traceback.print_exc()




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
        active_comps = comps.filter(is_active=True, processed=False).select_related('pd_code')
        for comp in active_comps:
            amt = Decimal(str(comp.amount))
            pd = getattr(comp, 'pdcode', getattr(comp, 'pd_code', None))
            if pd and pd.pdcode_code:
                code = pd.pdcode_code
                is_deduction = str(getattr(pd, 'category', '')).upper() == 'DEDUCTION'
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

    def _build_return(self, net_pay, er_cost=0):
        return {
            'breakdown': self.breakdown,
            'elements': self.results_dict,
            'pd_codes': self.pd_codes,
            'totals': {
                'gross': self.results_dict.get('5000', 0), 
                'net': net_pay
            },
            'ER Cost': {
                'ER Cost': self.results_dict.get('9000', 0), 
                'er_gross': er_cost
            }
        }