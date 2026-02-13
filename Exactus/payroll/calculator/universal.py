# Exactus/payroll/calculator/universal.py
import importlib
import logging
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q

from Exactus.payroll.calculator.base import BasePayrollCalculator
from Exactus.payroll.calculator.engine import TaxEngine

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


TWOPLACES = Decimal("0.01")


class UniversalPayrollCalculator(BasePayrollCalculator):
    """
    Universal Payroll Calculator

    Fixes included:
    - 6001/7001 "doubling" was caused by 6000/7000 totals being registered with opposite sign.
      Totals now match the sign convention of underlying codes (deductions negative).
    - 9001 employer cost % mismatch: for 9xxx rules we calculate progressive tax locally
      using CalculationBase bracket/rate fields to avoid TaxEngine quirks for employer costs.
    - 9000/7000/6000 mapping is consistent with 6001 / NI category subcodes / ER-NI subcodes.
    """

    def __init__(self, employee, period, **kwargs):
        super().__init__(employee, period, **kwargs)

        self.total_gross = Decimal("0.00")
        self.taxable_gross = Decimal("0.00")
        self.total_deductions = Decimal("0.00")

        self.pd_codes = []
        self.deduction_codes = set()
        self.salary_sacrifice_codes = set()

        # override container
        self.explicit_overrides = set()

        # active subcodes
        self.active_ni_code = "7001"
        self.active_er_ni_code = "9001"

        # country slug mapping
        self.country_slug = ""
        if self.period and self.period.payroll and self.period.payroll.country:
            raw_slug = (self.period.payroll.country.slug or "").lower().strip()
            if raw_slug == "united-kingdom":
                self.country_slug = "gb"
            else:
                self.country_slug = raw_slug.replace("-", "_")

    # ──────────────────────────────────────────────────────────────
    # MAIN ENTRY
    # ──────────────────────────────────────────────────────────────
    def calculate(self):
        self.results_dict = {}
        self.breakdown = []
        self.explicit_overrides = set()

        # defaults per run
        self.active_ni_code = "7001"
        self.active_er_ni_code = "9001"

        # 1) Aggregate compensations into results_dict (+bases)
        self._aggregate_compensations()

        # 2) Collect UI PD codes
        self._collect_pd_codes()

        # 3) Gross
        self._calculate_gross_pay()

        # 4) Determine subcodes for NI + ER NI BEFORE rules
        self._set_active_reporting_subcodes()

        # 5) Country nuances strategy (may set overrides, bases, etc.)
        self._apply_country_nuances()

        # 6) CalculationBase rules
        if self.period and self.period.payroll and CALCULATION_BASE_AVAILABLE:
            self._apply_calculation_rules()

        # 7) Consolidation totals
        self._consolidate_reporting_codes()

        # 8) Final Net (user formula)
        gross_val = self.results_dict.get("5000", Decimal("0.00"))
        tax_total = self.results_dict.get("6000", Decimal("0.00"))
        ni_total = self.results_dict.get("7000", Decimal("0.00"))

        other_deductions = Decimal("0.00")

        tax_codes_rolled_up = {"6001", "6002", "6100", "6200", "6300"}
        ni_codes_rolled_up = {"7001", "7010", "7020", "7030", "7040", "7050", "7060"}

        for code, val in self.results_dict.items():
            try:
                if not val:
                    continue
                code_str = str(code).strip()
                code_int = int(code_str)

                # Skip totals
                if code_str in {"6000", "7000", "9000"}:
                    continue

                # Skip components already in totals
                if code_str in tax_codes_rolled_up or code_str in ni_codes_rolled_up:
                    continue

                # Only employee deductions ranges (exclude 9000s employer costs)
                in_tax_other_range = (6400 <= code_int <= 6999)
                in_ni_other_range = (7400 <= code_int <= 7999)

                if in_tax_other_range or in_ni_other_range:
                    other_deductions += abs(val)
            except (ValueError, TypeError):
                continue

        net_pay = (gross_val - abs(tax_total) - abs(ni_total) - abs(other_deductions)).quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )

        # Store net
        self.results_dict["8000"] = Decimal("0.00")
        self.results_dict["88000"] = Decimal("0.00")
        self.results_dict["98000"] = Decimal("0.00")

        self.register("Net Salary", net_pay, "8000")
        self.results_dict["88000"] = net_pay
        self.results_dict["98000"] = net_pay

        return self._build_return(net_pay)

    # ──────────────────────────────────────────────────────────────
    # SUBCODE SETUP
    # ──────────────────────────────────────────────────────────────
    def _set_active_reporting_subcodes(self):
        ni_category = getattr(self.employee, "tax_info_05", "A") or "A"
        cat = str(ni_category).upper().strip()

        ni_map = {
            "A": "7001", "B": "7010", "C": "7020", "H": "7030",
            "J": "7040", "M": "7050", "Z": "7060",
        }
        er_ni_map = {
            "A": "9001", "B": "9010", "C": "9020", "H": "9030",
            "J": "9040", "M": "9050", "Z": "9060",
        }

        self.active_ni_code = ni_map.get(cat, "7001")
        self.active_er_ni_code = er_ni_map.get(cat, "9001")

    # ──────────────────────────────────────────────────────────────
    # GROSS (5000)
    # ──────────────────────────────────────────────────────────────
    def _calculate_gross_pay(self):
        gross_sum = Decimal("0.00")

        for code, val in self.results_dict.items():
            try:
                if not val:
                    continue
                code_int = int(str(code).strip())

                # earnings
                if 1000 <= code_int <= 1999:
                    gross_sum += val
                # deductions inside gross bands
                elif 2000 <= code_int <= 2999:
                    gross_sum -= abs(val)
                # other income bands
                elif 3000 <= code_int <= 4999:
                    gross_sum += val
            except (ValueError, TypeError):
                continue

        gross_sum = gross_sum.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        self.results_dict["5000"] = gross_sum

        # default taxable base if not populated by PD rules
        if "86000" not in self.results_dict or self.results_dict["86000"] == 0:
            self.results_dict["86000"] = gross_sum

    # ──────────────────────────────────────────────────────────────
    # PROGRESSIVE CALC FOR 9XXX (EMPLOYER COSTS)
    # ──────────────────────────────────────────────────────────────
    def _progressive_from_rule(self, base_val: Decimal, rule) -> Decimal:
        """
        Reads rule.bracket_00..bracket_15 and rule.rate_00..rate_15.
        Brackets are treated as UPPER bounds (cumulative bands).
        Rates are treated as percentages.
        """
        base_val = Decimal(base_val or 0)
        if base_val <= 0:
            return Decimal("0.00")

        brackets = []
        rates = []

        for i in range(16):
            b = getattr(rule, f"bracket_{i:02d}", None)
            r = getattr(rule, f"rate_{i:02d}", None)

            # stop if both missing
            if b is None and r is None:
                continue

            try:
                b_dec = Decimal(str(b)) if b is not None else None
                r_dec = Decimal(str(r)) if r is not None else Decimal("0")
            except Exception:
                continue

            if b_dec is None:
                # if bracket missing, we can't define band end; skip
                continue

            brackets.append(b_dec)
            rates.append(r_dec)

        if not brackets:
            return Decimal("0.00")

        tax = Decimal("0.00")
        prev = Decimal("0.00")

        for upper, pct in zip(brackets, rates):
            # defensive ordering
            if upper <= prev:
                continue

            if base_val <= prev:
                break

            portion = min(base_val, upper) - prev
            if portion > 0 and pct:
                tax += portion * (pct / Decimal("100"))

            prev = upper

        # remainder above last bracket uses last provided rate (common setup)
        if base_val > brackets[-1]:
            last_rate = rates[-1]
            if last_rate:
                tax += (base_val - brackets[-1]) * (last_rate / Decimal("100"))

        return tax.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    # ──────────────────────────────────────────────────────────────
    # CALCULATIONBASE RULES
    # ──────────────────────────────────────────────────────────────
    def _apply_calculation_rules(self):
        regulation = self.period.payroll.regulation
        period_freq = self.period.frequency

        rules = (
            CalculationBase.objects.filter(regulations=regulation, base_frequency=period_freq)
            .select_related("element", "element_base")
        )

        blocked_codes = {str(x).strip() for x in self.explicit_overrides}

        for rule in rules:
            try:
                if not rule.element:
                    continue

                target_code = str(rule.element.element_code).strip()

                # map totals -> effective subcodes (same approach as 6001/7001)
                effective_code = target_code
                if target_code == "6000":
                    effective_code = "6001"
                elif target_code == "7000":
                    effective_code = self.active_ni_code
                elif target_code == "9000":
                    effective_code = self.active_er_ni_code

                if effective_code in blocked_codes:
                    continue

                current_val = self.results_dict.get(effective_code, Decimal("0.00"))

                # Allow overwrite only for 9xxx; block overwrite otherwise
                if current_val != 0 and not str(effective_code).startswith("9"):
                    continue

                base_val = Decimal("0.00")

                # explicit base element in rule
                if rule.element_base:
                    base_code = str(rule.element_base.element_code).strip()  # IMPORTANT: keys are strings
                    base_val = self.results_dict.get(base_code, Decimal("0.00"))
                else:
                    # auto-base logic for employer costs
                    try:
                        eff_int = int(str(effective_code))
                        if 9001 <= eff_int <= 9399:
                            # 1) Try specific base "8{code}" e.g. 89001
                            auto_base = f"8{effective_code}"
                            base_val = self.results_dict.get(auto_base, Decimal("0.00"))

                            # 2) Try social security base
                            if base_val == 0:
                                base_val = self.results_dict.get("87000", Decimal("0.00"))

                            # 3) fallback gross
                            if base_val == 0:
                                base_val = self.results_dict.get("5000", Decimal("0.00"))
                    except Exception:
                        pass

                if base_val <= 0:
                    continue

                # Calculate
                if str(effective_code).startswith("9"):
                    # Employer costs: use local progressive (fixes 1% vs 15% issue)
                    calc_val = self._progressive_from_rule(base_val, rule)
                    if calc_val > 0:
                        # employer costs stored POSITIVE
                        self.register(rule.element.element_name, calc_val, effective_code)
                else:
                    # Employee deductions: use TaxEngine, store NEGATIVE
                    calc_val = TaxEngine.calculate_progressive_tax(base_val, rule)
                    try:
                        calc_val = Decimal(calc_val)
                    except Exception:
                        calc_val = Decimal("0.00")

                    if calc_val > 0:
                        self.register(rule.element.element_name, (-calc_val).quantize(TWOPLACES), effective_code)

            except Exception as e:
                logger.error(f"Error calculating rule {getattr(rule, 'id', '?')}: {e}")

    # ──────────────────────────────────────────────────────────────
    # CONSOLIDATION TOTALS (6000/7000/9000)
    # ──────────────────────────────────────────────────────────────
    def _consolidate_reporting_codes(self):
        # TAX: choose target detail code based on employee tax code
        raw_tax_code = getattr(self.employee, "tax_info_03", "BR") or "BR"
        clean_tax_code = str(raw_tax_code).upper().strip()

        # remove GB prefixes
        if self.country_slug == "gb" and (clean_tax_code.startswith("S") or clean_tax_code.startswith("C")):
            clean_tax_code = clean_tax_code[1:]

        target_tax_code = "6001"
        if clean_tax_code.startswith("BR"):
            target_tax_code = "6100"
        elif clean_tax_code.startswith("D0"):
            target_tax_code = "6200"
        elif clean_tax_code.startswith("D1"):
            target_tax_code = "6300"

        total_tax = self.results_dict.get(target_tax_code, Decimal("0.00"))
        if total_tax == 0:
            total_tax = self.results_dict.get("6002", Decimal("0.00"))

        # NI: use active employee NI code
        total_ni = self.results_dict.get(self.active_ni_code, Decimal("0.00"))

        # Employer costs: sum 9001-9399 (stored positive)
        total_er_cost = Decimal("0.00")
        for code, val in self.results_dict.items():
            if not val:
                continue
            try:
                c_int = int(str(code).strip())
                if 9001 <= c_int <= 9399:
                    total_er_cost += Decimal(val)
            except (ValueError, TypeError):
                continue

        total_tax = Decimal(total_tax).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        total_ni = Decimal(total_ni).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        total_er_cost = Decimal(total_er_cost).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

        # Reset totals first
        for key in ("6000", "7000", "9000"):
            self.results_dict[key] = Decimal("0.00")

        # IMPORTANT FIX:
        # totals now match the underlying sign convention:
        # - tax/NI deductions are negative
        # - employer costs are positive
        self._register_total("6000", "PAYE Income Tax Total", -total_tax)
        self._register_total("7000", "National Insurance Total", -total_ni)
        self._register_total("9000", "Total Employer Cost", total_er_cost)

    def _register_total(self, code, name, amount):
        amount = Decimal(amount).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        self.results_dict[str(code)] = amount

        found = False
        for b in self.breakdown:
            if str(b.get("code")) == str(code):
                b["amount"] = amount
                b["name"] = name
                found = True
                break

        if not found and amount != 0:
            self.breakdown.append({"name": name, "amount": amount, "code": str(code)})

    # ✅ Add inside UniversalPayrollCalculator (e.g. after _register_total)

    def _d(self, v):
        try:
            return Decimal(str(v or "0.00"))
        except Exception:
            return Decimal("0.00")

    def get_amount(self, code, default="0.00"):
        code = str(code).strip()
        return self._d(self.results_dict.get(code, default))

    def force_set(self, code, name, amount):
        """
        Hard-set a code value AND prevent CalculationBase from overwriting it.
        This is what you need for spreadsheet-style totals like 7001/86000/6100.
        """
        code = str(code).strip()
        amount = Decimal(amount).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

        # lock
        self.explicit_overrides.add(code)

        # set value
        self.results_dict[code] = amount

        # keep breakdown consistent (so UI shows correct figures)
        self._register_total(code, name, amount)


    # ──────────────────────────────────────────────────────────────
    # COUNTRY STRATEGY
    # ──────────────────────────────────────────────────────────────
    def _apply_country_nuances(self):
        if not self.country_slug:
            return

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

        except Exception as e:
            logger.warning(f"Nuance Error: {e}")

    # ──────────────────────────────────────────────────────────────
    # COMPENSATIONS / PD CODES
    # ──────────────────────────────────────────────────────────────
    def _get_compensation_list(self):
        if hasattr(self.employee, "compensation_components"):
            return getattr(self.employee, "compensation_components")
        if hasattr(self.employee, "compensationcomponent_set"):
            return getattr(self.employee, "compensationcomponent_set")
        for attr in ("compensations", "components"):
            if hasattr(self.employee, attr):
                return getattr(self.employee, attr)
        return None

    def _collect_pd_codes(self):
        comps = self._get_compensation_list()
        if not comps:
            return

        active_comps = comps.filter(is_active=True, processed=False)

        if self.period and getattr(self.period, "is_additional", False):
            active_comps = active_comps.filter(Q(category="VARIABLE") | Q(frequency="one_time"))

        for c in active_comps:
            amount_to_show = c.amount
            if self.period:
                amount_to_show = c.get_period_amount(self.period.start_date, self.period.end_date)

            pd = getattr(c, "pdcode", getattr(c, "pd_code", None))
            if pd:
                self.pd_codes.append(
                    {
                        "code": getattr(pd, "pdcode_code", ""),
                        "description": getattr(pd, "pdcode_description", ""),
                        "amount": amount_to_show,
                    }
                )

    def _aggregate_compensations(self):
        comps = self._get_compensation_list()
        if not comps:
            return

        active_comps = comps.filter(is_active=True, processed=False).select_related("pd_code")

        for comp in active_comps:
            amt = Decimal(str(comp.amount or 0)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

            pd = getattr(comp, "pdcode", getattr(comp, "pd_code", None))
            if not (pd and getattr(pd, "pdcode_code", None)):
                continue

            code = str(pd.pdcode_code).strip()
            is_deduction = str(getattr(pd, "category", "")).upper() == "DEDUCTION"

            # store the code itself (your system uses deductions sometimes as positive entries
            # and later applies abs() where needed; we keep your original behavior)
            self.results_dict[code] = self.results_dict.get(code, Decimal("0.00")) + amt
            if is_deduction:
                self.deduction_codes.add(code)

            # auto-bases 8xxx / 9xxx mirrors
            try:
                int(code)
                p_base = f"8{code}"
                y_base = f"9{code}"
                self.results_dict[p_base] = self.results_dict.get(p_base, Decimal("0.00")) + amt
                self.results_dict[y_base] = self.results_dict.get(y_base, Decimal("0.00")) + amt
            except Exception:
                pass

            explicit_bases_found = set()

            # explicit bases
            if hasattr(pd, "applicable_bases"):
                for base in pd.applicable_bases.all():
                    b_code = str(base.element_code).strip()
                    explicit_bases_found.add(b_code)

                    if is_deduction:
                        self.results_dict[b_code] = self.results_dict.get(b_code, Decimal("0.00")) - amt
                    else:
                        self.results_dict[b_code] = self.results_dict.get(b_code, Decimal("0.00")) + amt

            # payable base defaults
            if getattr(pd, "pdcode_payable", False) and not is_deduction:
                if "85000" not in explicit_bases_found:
                    self.results_dict["85000"] = self.results_dict.get("85000", Decimal("0.00")) + amt
                    self.results_dict["95000"] = self.results_dict.get("95000", Decimal("0.00")) + amt

            # taxable base defaults
            if getattr(pd, "pdcode_taxable", False):
                for base in ("86000", "86001"):
                    if base not in explicit_bases_found:
                        op_amt = -amt if is_deduction else amt
                        self.results_dict[base] = self.results_dict.get(base, Decimal("0.00")) + op_amt
                        self.results_dict[f"9{base[1:]}"] = self.results_dict.get(f"9{base[1:]}", Decimal("0.00")) + op_amt

            # social securitable base defaults
            if getattr(pd, "pdcode_social_securitable", False):
                for base in ("87000", "87001"):
                    if base not in explicit_bases_found:
                        op_amt = -amt if is_deduction else amt
                        self.results_dict[base] = self.results_dict.get(base, Decimal("0.00")) + op_amt
                        self.results_dict[f"9{base[1:]}"] = self.results_dict.get(f"9{base[1:]}", Decimal("0.00")) + op_amt

    # ──────────────────────────────────────────────────────────────
    # RETURN STRUCTURE
    # ──────────────────────────────────────────────────────────────
    def _build_return(self, net_pay, er_cost=0):
        return {
            "breakdown": self.breakdown,
            "elements": self.results_dict,
            "pd_codes": self.pd_codes,
            "totals": {
                "gross": self.results_dict.get("5000", 0),
                "net": net_pay,
            },
            "ER Cost": {
                "ER Cost": self.results_dict.get("9000", 0),
                "er_gross": er_cost,
            },
        }
