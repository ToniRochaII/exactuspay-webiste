from decimal import Decimal, ROUND_HALF_UP

from Exactus.payroll.calculator.countries.base import CountryPayrollStrategy


TWOPLACES = Decimal("0.01")


def d(v) -> Decimal:
    try:
        return Decimal(str(v or "0.00"))
    except Exception:
        return Decimal("0.00")


def q2(v: Decimal) -> Decimal:
    return d(v).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


class ChilePayrollStrategy(CountryPayrollStrategy):
    """
    Chile Hook (CL)

    Plugs into:
      UniversalPayrollCalculator._apply_country_nuances()
        -> imports Exactus.payroll.calculator.countries.cl.calculator
        -> finds *PayrollStrategy class
        -> runs process_nuances()

    This strategy:
      - Reads taxable income base from 86000 (already produced by Universal aggregation).
      - Calculates Chile-style statutory deductions (simplified v1).
      - Registers:
          * Income tax under 6002 (so Universal totals pick it up)
          * Social contributions total under 7001 (so Universal totals pick it up)
          * Employer costs under 900x (so Universal totals pick them up)
      - Locks overrides to prevent CalculationBase from overwriting these figures.
    """

    # --- Default statutory rates (v1 placeholders you can later drive from DB/CalculationBase) ---
    AFP_PENSION_RATE = Decimal("0.10")        # Employee pension (AFP)
    HEALTH_RATE = Decimal("0.07")             # Employee health (FONASA/ISAPRE base)
    UNEMP_EMP_RATE = Decimal("0.006")         # Employee unemployment (indefinite contracts)
    UNEMP_ER_RATE = Decimal("0.024")          # Employer unemployment (indefinite contracts)
    SIS_ER_RATE = Decimal("0.015")            # Employer SIS (approx / varies)
    ACCIDENT_ER_RATE_DEFAULT = Decimal("0.010")  # Employer accident/risk insurance (varies by activity)

    def process_nuances(self):
        calc = self.calc
        emp = getattr(calc, "employee", None)
        results = getattr(calc, "results_dict", {})  # same dict as in Universal

        taxable_income = d(results.get("86000", "0.00"))
        if taxable_income <= 0:
            return

        # 1) Determine contract type (best-effort)
        # Accepts: employee.contract_type, employee.employment_type, employee.tax_info_XX etc.
        # If unknown, assume indefinite (most common) so system behaves predictably.
        contract_type = (
            str(getattr(emp, "contract_type", "") or getattr(emp, "employment_type", "") or "")
            .strip()
            .lower()
        )
        is_fixed_term = contract_type in {"fixed", "fixed_term", "temporary", "temp", "plazo_fijo", "plazo-fijo"}
        is_indefinite = not is_fixed_term  # default

        # 2) Optional per-employee/provider variations (best-effort)
        # AFP fee varies per AFP; if you store it somewhere, we’ll use it.
        # Example fields: afp_fee_rate, pension_admin_fee_rate
        afp_fee_rate = d(getattr(emp, "afp_fee_rate", None) or getattr(emp, "pension_admin_fee_rate", None) or "0.00")

        # Accident insurance varies by risk class; allow employee/company override if present
        accident_er_rate = d(
            getattr(emp, "accident_er_rate", None)
            or getattr(emp, "work_risk_rate", None)
            or self.ACCIDENT_ER_RATE_DEFAULT
        )

        # 3) Employee deductions (computed on taxable base in v1)
        afp_pension = q2(taxable_income * self.AFP_PENSION_RATE)
        afp_fee = q2(taxable_income * afp_fee_rate) if afp_fee_rate > 0 else Decimal("0.00")
        health = q2(taxable_income * self.HEALTH_RATE)

        unemp_emp = Decimal("0.00")
        if is_indefinite:
            unemp_emp = q2(taxable_income * self.UNEMP_EMP_RATE)

        # 4) Employer costs
        unemp_er = Decimal("0.00")
        if is_indefinite:
            unemp_er = q2(taxable_income * self.UNEMP_ER_RATE)

        sis_er = q2(taxable_income * self.SIS_ER_RATE)
        accident_er = q2(taxable_income * accident_er_rate)

        # 5) Income tax (Impuesto Único) – simplified progressive example (REPLACE WITH DB RULES)
        # IMPORTANT: This is a placeholder bracket table so the engine works end-to-end.
        # You’ll likely want this driven by CalculationBase with monthly brackets (UTM-indexed).
        income_tax = self._calculate_income_tax_placeholder(taxable_income)

        # 6) Register deductions using the same conventions as Brazil:
        # - employee deductions are NEGATIVE
        # - employer costs are POSITIVE
        #
        # We also set/lock totals so Universal doesn’t override and consolidation is correct.

        # Income tax -> 6002 (so Universal uses it for 6000 total)
        if income_tax != 0:
            calc.register("Income Tax (Chile)", -income_tax, "6002")
            calc.explicit_overrides.add("6002")
            calc.explicit_overrides.add("6000")  # keep 6000 consistent with our tax

        # Social contributions -> we itemize AND set 7001 as the combined total
        # Item codes (74xx) are optional; they will still reduce net as "other deductions"
        # but we ALSO want 7000 total populated, so we set 7001 as the sum.
        social_total = Decimal("0.00")

        if afp_pension != 0:
            calc.register("AFP Pension (10%)", -afp_pension, "7401")
            social_total += afp_pension

        if afp_fee != 0:
            calc.register("AFP Admin Fee", -afp_fee, "7402")
            social_total += afp_fee

        if health != 0:
            calc.register("Health (7%)", -health, "7403")
            social_total += health

        if unemp_emp != 0:
            calc.register("Unemployment (Employee)", -unemp_emp, "7404")
            social_total += unemp_emp

        # Force 7001 = total social contributions (so Universal 7000 will show deductions)
        if social_total != 0:
            # Store as POSITIVE in 7001 because Universal consolidator flips sign when writing 7000
            # (it does: _register_total("7000", ..., -total_ni))
            calc.force_set("7001", "Social Security Total (CL)", q2(social_total))
            calc.explicit_overrides.add("7001")
            calc.explicit_overrides.add("7000")

        # Employer costs -> 900x (these get summed into 9000 total automatically)
        if unemp_er != 0:
            calc.register("Unemployment (Employer)", unemp_er, "9002")
            calc.explicit_overrides.add("9002")

        if sis_er != 0:
            calc.register("SIS (Employer)", sis_er, "9003")
            calc.explicit_overrides.add("9003")

        if accident_er != 0:
            calc.register("Accident Insurance (Employer)", accident_er, "9004")
            calc.explicit_overrides.add("9004")

        # Done. Universal will later consolidate totals and compute net.

    def _calculate_income_tax_placeholder(self, base: Decimal) -> Decimal:
        """
        Placeholder progressive monthly tax.
        Replace with Chile's real Impuesto Único brackets (usually UTM-based) via CalculationBase.

        Table below is intentionally simple so your engine runs.
        """
        base = d(base)
        if base <= 0:
            return Decimal("0.00")

        # Example bands (CLP) – NOT official, for plumbing only:
        # (upper_limit, rate)
        bands = [
            (Decimal("800000"), Decimal("0.00")),
            (Decimal("1500000"), Decimal("0.04")),
            (Decimal("2500000"), Decimal("0.08")),
            (Decimal("3500000"), Decimal("0.135")),
            (Decimal("5000000"), Decimal("0.23")),
            (Decimal("7000000"), Decimal("0.304")),
            (Decimal("9000000"), Decimal("0.35")),
        ]
        top_rate = Decimal("0.40")

        remaining = base
        last_limit = Decimal("0.00")
        tax = Decimal("0.00")

        for upper, rate in bands:
            if remaining <= 0:
                break
            span = upper - last_limit
            chunk = min(remaining, span)
            tax += chunk * rate
            remaining -= chunk
            last_limit = upper

        if remaining > 0:
            tax += remaining * top_rate

        return q2(tax)