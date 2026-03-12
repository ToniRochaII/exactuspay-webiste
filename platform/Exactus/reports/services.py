# Exactus/reports/services.py

from decimal import Decimal
from collections import defaultdict
import json
from django.apps import apps
from django.db.models import Q

# ---------------------------------------------------------------------
# Safe helpers
# ---------------------------------------------------------------------

def _safe_json(details):
    if isinstance(details, dict):
        return details
    if isinstance(details, str):
        try:
            return json.loads(details)
        except Exception:
            return {}
    return {}

def _money(x) -> Decimal:
    try:
        return Decimal(str(x or "0"))
    except Exception:
        return Decimal("0")

def _int_or_none(x):
    try:
        return int(str(x).strip())
    except Exception:
        return None

def _has_field(model_cls, field_name: str) -> bool:
    return any(getattr(f, "name", None) == field_name for f in getattr(model_cls, "_meta", []).fields)

# ---------------------------------------------------------------------
# Map Builders
# ---------------------------------------------------------------------

def build_label_maps(country=None, company=None):
    """
    Fetches names and descriptions for Elements and PD Codes to populate
    friendly labels in the report.
    """
    element_map = {}
    pdcode_map = {}

    # Elements
    try:
        Element = apps.get_model("elements", "Element")
        qs = Element.objects.all()

        if country and _has_field(Element, "country"):
            qs = qs.filter(country=country)
        if company and _has_field(Element, "company"):
            qs = qs.filter(company=company)

        for el in qs:
            code = getattr(el, "element_code", getattr(el, "code", None))
            if code is None:
                continue
            name = (getattr(el, "element_name", getattr(el, "name", None)) or "").strip()
            desc = (getattr(el, "element_description", getattr(el, "description", None)) or "").strip()
            element_map[str(code)] = {"name": name, "description": desc}
    except Exception:
        pass

    # PD Codes
    try:
        PDcode = apps.get_model("pdcodes", "PDcode")
        qs = PDcode.objects.all()

        if country and _has_field(PDcode, "country"):
            qs = qs.filter(country=country)
        if company and _has_field(PDcode, "company"):
            qs = qs.filter(company=company)

        for pd in qs:
            code = getattr(pd, "pdcode_code", getattr(pd, "code", None))
            if code is None:
                continue
            name = (getattr(pd, "pdcode_name", getattr(pd, "name", None)) or "").strip()
            desc = (getattr(pd, "pdcode_description", getattr(pd, "description", None)) or "").strip()
            pdcode_map[str(code)] = {"name": name, "description": desc}
    except Exception:
        pass

    return element_map, pdcode_map


def build_hidden_maps(country=None, company=None):
    """
    Returns a set of codes (strings) that are explicitly marked as 'Hidden'.
    Everything else is assumed to be visible.
    """
    hidden_codes = set()

    # PD Codes
    try:
        PDcode = apps.get_model("pdcodes", "PDcode")
        # Only fetch items explicitly marked as Hidden
        if _has_field(PDcode, "pdcode_status"):
            pd_qs = PDcode.objects.filter(pdcode_status__iexact="Hidden")

            if country and hasattr(PDcode, "country_id"):
                pd_qs = pd_qs.filter(country=country)
            if company and hasattr(PDcode, "company_id"):
                pd_qs = pd_qs.filter(company=company)

            for pd in pd_qs:
                code = getattr(pd, "pdcode_code", getattr(pd, "code", None))
                if code is not None:
                    hidden_codes.add(str(code))
    except Exception:
        pass

    # Elements
    try:
        Element = apps.get_model("elements", "Element")
        # Only fetch items explicitly marked as Hidden
        if _has_field(Element, "element_status"):
            el_qs = Element.objects.filter(element_status__iexact="Hidden")

            if country and hasattr(Element, "country_id"):
                el_qs = el_qs.filter(country=country)
            if company and hasattr(Element, "company_id"):
                el_qs = el_qs.filter(company=company)

            for el in el_qs:
                code = getattr(el, "element_code", getattr(el, "code", None))
                if code is not None:
                    hidden_codes.add(str(code))
    except Exception:
        pass

    return hidden_codes

# ---------------------------------------------------------------------
# Comparison Report Logic
# ---------------------------------------------------------------------

def build_gross_to_net_comparison_rows(
    *,
    current_results,
    previous_results,
    current_period,
    previous_period,
    country=None,
    company=None,
    hidden_codes: set = None,  # CHANGED: Now accepts a blacklist of hidden codes
    element_map: dict = None,
    pdcode_map: dict = None,
):
    """
    Output layout like COMPARISONREPORTSYSTEM001 (4).csv:
    Company_id, Id, Period, Employee, Code, Description, Current Period, Previous Period, Balance
    
    Logic: Includes all codes 1000-9999 unless they appear in 'hidden_codes'.
    """

    if hidden_codes is None: hidden_codes = set()
    if element_map is None: element_map = {}
    if pdcode_map is None: pdcode_map = {}

    # employee_id -> PayrollResult
    cur_by_emp = {r.employee_id: r for r in current_results}
    prev_by_emp = {r.employee_id: r for r in previous_results}

    all_emp_ids = sorted(set(cur_by_emp.keys()) | set(prev_by_emp.keys()))
    rows = []

    def extract_lines(result):
        """
        Returns:
          ordered_keys: [(code_int, description_str), ...] preserving source order
          amount_map: {(code_int, description_str): Decimal}
        """
        d = _safe_json(getattr(result, "details", None))
        amount_map = defaultdict(lambda: Decimal("0"))
        ordered_keys = []

        def add(code_int, desc, amt):
            if code_int is None:
                return
            
            # ---------------------------------------------------
            # RULE 1: Range Check (1000 - 9999)
            # ---------------------------------------------------
            if not (1000 <= code_int <= 9999):
                return

            code_str = str(code_int)

            # ---------------------------------------------------
            # RULE 2: Hidden Status Check
            # ---------------------------------------------------
            if code_str in hidden_codes:
                return

            # Resolve Description
            if not desc:
                # Try Element Map first
                if code_str in element_map:
                    desc = element_map[code_str].get('name', '')
                # Try PD Code Map second
                elif code_str in pdcode_map:
                    desc = pdcode_map[code_str].get('name', '')
            
            # Fallback
            desc = (desc or "").strip() or f"Code {code_int}"

            key = (int(code_int), desc)
            if key not in amount_map:
                ordered_keys.append(key)
            amount_map[key] += _money(amt)

        # 1) PD CODES (List)
        pd_list = d.get("pd_codes") or d.get("pdcodes") or []
        if isinstance(pd_list, list):
            for item in pd_list:
                if not isinstance(item, dict):
                    continue
                code = _int_or_none(item.get("code"))
                desc = (
                    item.get("description")
                    or item.get("name")
                    or item.get("label")
                    or ""
                )
                add(code, desc, item.get("amount"))

        # 2) ELEMENTS (Dict)
        el = d.get("elements") or {}
        if isinstance(el, dict):
            for k, v in el.items():
                code = _int_or_none(k)
                # Pass empty string for desc; 'add' will resolve it via element_map
                add(code, "", v)

        # 3) Hardcoded Totals (Always Visible if within range/not hidden)
        # We try to add these. The 'add' function will internally check
        # if 5000/8000 are hidden or out of range.
        add(5000, "Gross Pay", getattr(result, "gross_pay", 0))
        add(8000, "Net salary", getattr(result, "net_pay", 0))

        return ordered_keys, dict(amount_map)

    def company_id_for(res):
        if company and hasattr(company, "company_code"):
            return company.company_code
        try:
            return res.period.payroll.company.company_code
        except Exception:
            return ""

    for emp_id in all_emp_ids:
        cur = cur_by_emp.get(emp_id)
        prev = prev_by_emp.get(emp_id)
        any_res = cur or prev
        emp = any_res.employee

        emp_name = (
            f"{getattr(emp, 'first_name', '')} {getattr(emp, 'last_name', '')}".strip()
            or str(emp)
        )
        emp_display = emp_name
        if company and getattr(company, "name", None):
            emp_display = f"{emp_name} ({company.name})"

        cur_order, cur_map = extract_lines(cur) if cur else ([], {})
        prev_order, prev_map = extract_lines(prev) if prev else ([], {})

        # Merge keys: stable ordering
        ordered_keys = list(cur_order)
        for k in prev_order:
            if k not in ordered_keys:
                ordered_keys.append(k)
        
        ordered_keys = sorted(ordered_keys, key=lambda k: k[0])

        for (code_int, desc) in ordered_keys:
            cur_amt = _money(cur_map.get((code_int, desc), 0))
            prev_amt = _money(prev_map.get((code_int, desc), 0))
            bal = cur_amt - prev_amt

            rows.append({
                "Company_id": company_id_for(any_res),
                "Id": getattr(emp, "employee_id", emp_id),
                "Period": str(current_period),
                "Employee": emp_display,
                "Code": str(code_int),
                "Description": desc,
                "Current Period": cur_amt,
                "Previous Period": prev_amt,
                "Balance": bal,
            })

    return rows


