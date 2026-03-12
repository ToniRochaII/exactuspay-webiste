# Exactus/reports/views.py
from __future__ import annotations

from .engine import ReportEngine
from .services import build_gross_to_net_comparison_rows

from datetime import datetime
import json
from decimal import Decimal

from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView


from .models import ReportConfiguration, ReportCategory, ReportType, ReportLayout
from .forms import ReportTypeForm, ReportLayoutForm, ReportConfigForm

from .utils import render_to_pdf, render_to_csv

from Exactus.payroll.models import PayrollPeriod, PeriodStatus


# =========================================================
# 0) PERMISSIONS
# =========================================================

def can_edit(user) -> bool:
    allowed_roles = {"Executive", "Admin", "Implementation", "Operation", "Compliance"}
    if getattr(user, "is_superuser", False):
        return True
    if hasattr(user, "role"):
        return str(user.role) in allowed_roles
    return False


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return can_edit(self.request.user)


# =========================================================
# 1) PERIOD HELPERS
# =========================================================

def get_processed_periods(country=None, company=None):
    qs = PayrollPeriod.objects.select_related("payroll").all()

    if company:
        qs = qs.filter(payroll__company=company)

    if country:
        qs = qs.filter(payroll__country=country)

    # Removed the status filter so it returns periods in ANY status
    return qs.order_by("-payment_date", "-id")


# =========================================================
# 2) PAYSLIP CONSTANTS
# =========================================================

EXCLUDE_ITEMISED_CODES = {5000, 8000}

# Hide sub-codes completely based on your setup
HIDE_CODE_BANDS = [
    (6001, 6399),
    (7001, 7399),
]


# =========================================================
# 3) SAFE HELPERS
# =========================================================

def safe_json(details):
    if isinstance(details, dict):
        return details
    if isinstance(details, str):
        try:
            return json.loads(details)
        except Exception:
            return {}
    return {}

def money(x) -> Decimal:
    try:
        return Decimal(str(x or "0"))
    except Exception:
        return Decimal("0")

def int_or_none(x):
    try:
        return int(str(x).strip())
    except Exception:
        return None

def is_visible(item) -> bool:
    if not isinstance(item, dict):
        return True

    if "is_visible" in item:
        return bool(item.get("is_visible"))

    if "visible" in item:
        return bool(item.get("visible"))

    status = item.get("status", None)
    if status is None:
        return True

    if isinstance(status, bool):
        return status

    if isinstance(status, str):
        s = status.strip().lower()
        if s in {"hidden", "hide", "false", "no", "0"}:
            return False
        if s in {"visible", "show", "true", "yes", "1"}:
            return True

    return True

def make_row(code_int, name, amount, ytd_val=Decimal("0")):
    return {
        "code": str(code_int),
        "name": name or "-",
        "amount": money(amount),
        "ytd": money(ytd_val),
    }


# =========================================================
# 4) DB LABEL MAPS
# =========================================================

def _has_field(model_cls, field_name: str) -> bool:
    return any(getattr(f, "name", None) == field_name for f in getattr(model_cls, "_meta", []).fields)

def build_label_maps(country=None, company=None):
    element_map = {}
    pdcode_map = {}

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
    except Exception as e:
        print(f"DEBUG - Element lookup failed: {e}")

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
    except Exception as e:
        print(f"DEBUG - PDcode lookup failed: {e}")

    return element_map, pdcode_map


def resolve_db_label(code_int, element_map, pdcode_map, prefer="description") -> str:
    code_key = str(code_int) if code_int is not None else ""
    if not code_key:
        return "Code"

    fallback_map = {
        "6000": "Income Tax",
        "7000": "Social Security",
        "8000": "Student Loan",
        "8001": "Postgraduate Loan",
        "9000": "Employer NI",
        "9001": "Employer Pension"
    }

    el = element_map.get(code_key)
    if el:
        primary = (el.get(prefer) or "").strip()
        secondary = (el.get("description" if prefer == "name" else "name") or "").strip()
        if primary: return primary
        if secondary: return secondary

    pd = pdcode_map.get(code_key)
    if pd:
        primary = (pd.get(prefer) or "").strip()
        secondary = (pd.get("description" if prefer == "name" else "name") or "").strip()
        if primary: return primary
        if secondary: return secondary

    fallback = fallback_map.get(code_key)
    if fallback:
        return fallback

    return f"Code {code_key}"


# =========================================================
# 5) PAYSLIP BUILDER (WITH COUNTRY FORMATTING)
# =========================================================

def build_payslips(results, *, country=None, company=None, prefer_label="description"):
    element_map, pdcode_map = build_label_maps(country=country, company=company)

    # Extract Country Settings
    c_fmt = getattr(country, 'numbering_format', "1,000.00") if country else "1,000.00"
    c_pos = getattr(country, 'currency_position', "BEFORE") if country else "BEFORE"
    c_dec = getattr(country, 'decimals', 2) if country else 2
    c_code = getattr(country, 'currency_code', "£") if country else "£"
    d_fmt_setting = getattr(country, 'date_format', "DD/MM/YYYY") if country else "DD/MM/YYYY"

    date_mapping = {
        "DD/MM/YYYY": "%d/%m/%Y",
        "MM/DD/YYYY": "%m/%d/%Y",
        "YYYY/MM/DD": "%Y/%m/%d",
        "YYYY/DD/MM": "%Y/%d/%m",
    }
    strftime_fmt = date_mapping.get(d_fmt_setting, "%d/%m/%Y")

    def fmt_num(val):
        v = money(val)
        s = f"{v:,.{c_dec}f}"
        if c_fmt == "1.000,00":
            s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return s

    def fmt_cur(val):
        s = fmt_num(val)
        if c_pos == "AFTER":
            return f"{s} {c_code}"
        return f"{c_code} {s}"

    payslips = []

    for res in results:
        d = safe_json(getattr(res, "details", None))

        pd_codes = d.get("pd_codes", d.get("pdcodes", []))
        elements = d.get("elements", d.get("statutory", []))

        earnings = []
        deductions = []
        employer_costs = []

        used_codes = set()

        def add_to_bucket(row, code_int: int):
            if 1000 <= code_int <= 4999:
                earnings.append(row)
                return
            if 6000 <= code_int <= 7999:
                row["amount"] = abs(money(row["amount"]))
                row["ytd"] = abs(money(row["ytd"]))
                deductions.append(row)
                return
            if code_int >= 9000:
                employer_costs.append(row)
                return

            if money(row["amount"]) < 0:
                row["amount"] = abs(money(row["amount"]))
                row["ytd"] = abs(money(row["ytd"]))
                deductions.append(row)
            else:
                earnings.append(row)

        if isinstance(pd_codes, list):
            for item in pd_codes:
                if not is_visible(item): continue

                code_int = int_or_none(item.get("code"))
                if code_int is None or code_int in EXCLUDE_ITEMISED_CODES: continue

                hidden = False
                for start, end in HIDE_CODE_BANDS:
                    if start <= code_int <= end:
                        hidden = True
                        break
                if hidden: continue

                used_codes.add(code_int)
                display_name = resolve_db_label(code_int, element_map, pdcode_map, prefer=prefer_label)

                row = make_row(code_int, display_name, item.get("amount"), item.get("ytd"))
                add_to_bucket(row, code_int)

        if isinstance(elements, list):
            element_items = elements
        elif isinstance(elements, dict):
            element_items = [{"code": k, "amount": v} for k, v in elements.items()]
        else:
            element_items = []

        for item in element_items:
            if not is_visible(item): continue

            code_int = int_or_none(item.get("code"))
            if code_int is None or code_int in EXCLUDE_ITEMISED_CODES: continue

            hidden = False
            for start, end in HIDE_CODE_BANDS:
                if start <= code_int <= end:
                    hidden = True
                    break
            if hidden: continue

            if code_int in used_codes: continue

            display_name = resolve_db_label(code_int, element_map, pdcode_map, prefer=prefer_label)

            row = make_row(code_int, display_name, item.get("amount"), item.get("ytd"))
            add_to_bucket(row, code_int)

        def sort_key(r):
            return int_or_none(r.get("code")) or 999999

        earnings.sort(key=sort_key)
        deductions.sort(key=sort_key)
        employer_costs.sort(key=sort_key)

        for r in earnings + deductions + employer_costs:
            r["fmt_amount"] = fmt_num(r["amount"])
            r["fmt_ytd"] = fmt_num(r["ytd"])

        total_gross = sum((money(i["amount"]) for i in earnings), Decimal("0"))
        total_ded = sum((money(i["amount"]) for i in deductions), Decimal("0"))
        net_pay = total_gross - total_ded

        ytd_summary = d.get("ytd_summary", {})
        if not isinstance(ytd_summary, dict):
            ytd_summary = {}
            
        run_gross = getattr(res, "gross_pay", None)
        if run_gross is None: run_gross = total_gross
        run_ded = getattr(res, "total_deductions", None)
        if run_ded is None: run_ded = total_ded
        run_net = getattr(res, "net_pay", None)
        if run_net is None: run_net = net_pay

        dt = getattr(res.period, "payment_date", None)
        fmt_date = dt.strftime(strftime_fmt) if dt else "-"

        payslips.append({
            "run": res,
            "earnings": earnings,
            "deductions": deductions,
            "employer_costs": employer_costs,
            "total_gross": total_gross,
            "total_deductions": total_ded,
            "net_pay": net_pay,
            "ytd_summary": {
                "gross": money(ytd_summary.get("gross")),
                "tax": money(ytd_summary.get("tax")),
            },
            
            "fmt_date": fmt_date,
            "fmt_run_gross": fmt_num(run_gross),
            "fmt_run_ded": fmt_num(run_ded),
            "fmt_run_net_cur": fmt_cur(run_net),
            "fmt_ytd_gross": fmt_num(ytd_summary.get("gross", 0)),
            "fmt_ytd_tax": fmt_num(ytd_summary.get("tax", 0)),
        })

    return payslips


# =========================================================
# 6) DASHBOARDS
# =========================================================

class BaseReportDashboard(LoginRequiredMixin, View):
    template_name = "reports/dashboard_hierarchical.html"

    def get_common_context(self, request, country=None, company=None):
        processed_periods = get_processed_periods(country=country, company=company)

        selected_period_id = request.GET.get("period_id") or ""
        selected_period = processed_periods.filter(id=selected_period_id).first() if selected_period_id else None

        return {
            "categories": ReportCategory.objects.prefetch_related("reporttype_set").all(),
            "processed_periods": processed_periods,
            "selected_period_id": selected_period_id,
            "selected_period": selected_period,
        }


class SystemReportDashboard(BaseReportDashboard):
    def get(self, request):
        if not can_edit(request.user):
            raise PermissionDenied()

        configs = ReportConfiguration.objects.filter(level="SYSTEM")
        context = self.get_common_context(request)
        context.update({"scope": "SYSTEM", "configs": configs, "can_edit": True})
        return render(request, self.template_name, context)


class CountryReportDashboard(BaseReportDashboard):
    def get(self, request, country_slug):
        Country = apps.get_model("country", "Country")
        country = get_object_or_404(Country, slug=country_slug)

        system_configs = ReportConfiguration.objects.filter(level="SYSTEM")
        country_configs = ReportConfiguration.objects.filter(country=country, company__isnull=True)

        context = self.get_common_context(request, country=country)
        context.update({
            "scope": "COUNTRY",
            "target_country": country,
            "inherited_configs": system_configs,
            "scoped_configs": country_configs,
            "can_edit": can_edit(request.user),
        })
        return render(request, self.template_name, context)


class CompanyReportDashboard(BaseReportDashboard):
    def get(self, request, country_slug, company_id):
        Company = apps.get_model("company", "Company")
        company = get_object_or_404(Company, pk=company_id, country__slug=country_slug)

        system_configs = ReportConfiguration.objects.filter(level="SYSTEM")
        country_configs = ReportConfiguration.objects.filter(country=company.country, company__isnull=True)

        inherited = list(system_configs) + list(country_configs)
        company_configs = ReportConfiguration.objects.filter(company=company)

        context = self.get_common_context(request, country=company.country, company=company)
        context.update({
            "scope": "COMPANY",
            "target_company": company,
            "target_country": company.country,
            "inherited_configs": inherited,
            "scoped_configs": company_configs,
            "can_edit": can_edit(request.user),
        })
        return render(request, self.template_name, context)


# =========================================================
# 7) MANAGEMENT HUB
# =========================================================

class ReportManagementHub(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        return render(request, "reports/management/hub.html", {
            "total_types": ReportType.objects.count(),
            "total_layouts": ReportLayout.objects.count(),
            "total_configs": ReportConfiguration.objects.count(),
        })


class ReportTypeListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = ReportType
    template_name = "reports/management/type_list.html"
    context_object_name = "types"


class ReportTypeCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = ReportType
    form_class = ReportTypeForm
    template_name = "reports/management/form.html"
    success_url = reverse_lazy("manage_types_list")
    extra_context = {"title": "Add Report Type"}


class ReportTypeUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = ReportType
    form_class = ReportTypeForm
    template_name = "reports/management/form.html"
    success_url = reverse_lazy("manage_types_list")
    extra_context = {"title": "Edit Report Type"}


class ReportTypeDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = ReportType
    template_name = "reports/management/confirm_delete.html"
    success_url = reverse_lazy("manage_types_list")


class ReportLayoutListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = ReportLayout
    template_name = "reports/management/layout_list.html"
    context_object_name = "layouts"


class ReportLayoutCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = ReportLayout
    form_class = ReportLayoutForm
    template_name = "reports/management/form.html"
    success_url = reverse_lazy("manage_layouts_list")
    extra_context = {"title": "Upload Report Layout"}


class ReportLayoutUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = ReportLayout
    form_class = ReportLayoutForm
    template_name = "reports/management/form.html"
    success_url = reverse_lazy("manage_layouts_list")
    extra_context = {"title": "Edit Layout"}


class ReportLayoutDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = ReportLayout
    template_name = "reports/management/confirm_delete.html"
    success_url = reverse_lazy("manage_layouts_list")


class ReportConfigListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = ReportConfiguration
    template_name = "reports/management/config_list.html"
    context_object_name = "configs"


class ReportConfigCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = ReportConfiguration
    form_class = ReportConfigForm
    template_name = "reports/management/form.html"
    success_url = reverse_lazy("manage_configs_list")
    extra_context = {"title": "Create Configuration Rule"}


class ReportConfigUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = ReportConfiguration
    form_class = ReportConfigForm
    template_name = "reports/management/form.html"
    success_url = reverse_lazy("manage_configs_list")
    extra_context = {"title": "Edit Configuration"}


class ReportConfigDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = ReportConfiguration
    template_name = "reports/management/confirm_delete.html"
    success_url = reverse_lazy("manage_configs_list")


# =========================================================
# 8) GENERATION ENGINE
# =========================================================

from django.apps import apps
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin


class GenerateReportView(LoginRequiredMixin, View):
    """
    Run a report for a specific processed period.
    Querystring: ?period_id=<PayrollPeriod.id>&format=html|pdf|csv
    """

    def get(self, request, report_code, company_id=None, country_slug=None):
        from .engine import ReportEngine
        from .services import build_gross_to_net_comparison_rows

        PayrollResult = apps.get_model("payroll", "PayrollResult")
        Company = apps.get_model("company", "Company")
        Country = apps.get_model("country", "Country")

        # -----------------------------
        # Resolve scope (country/company)
        # -----------------------------
        country = get_object_or_404(Country, slug=country_slug) if country_slug else None

        company = None
        if company_id:
            try:
                if int(company_id) != 0:
                    company = get_object_or_404(Company, pk=company_id)
            except (TypeError, ValueError):
                company = None

        # -----------------------------
        # Load report configuration
        # -----------------------------
        config = ReportEngine.get_configuration(report_code, company=company, country=country)
        if not config:
            return HttpResponse("No report layout found.", status=404)

        settings = getattr(config, "data_settings", {}) or {}
        if isinstance(settings, str):
            try:
                settings = json.loads(settings)
            except Exception:
                settings = {}

        report_mode = settings.get("report_mode") if isinstance(settings, dict) else None

        # ✅ Default comparison mode for this report if not configured
        if not report_mode and report_code == "COMPARISONREPORTSYSTEM001":
            report_mode = "comparison_gross_to_net"



        # -----------------------------
        # Read query params
        # -----------------------------
        export_format = (request.GET.get("format") or "html").lower().strip()
        period_id = request.GET.get("period_id")

        if not period_id:
            return HttpResponse("Please select a processed payroll period.", status=400)

        # -----------------------------
        # Resolve selected period
        # -----------------------------
        processed_periods = get_processed_periods(country=country, company=company)
        selected_period = processed_periods.filter(id=period_id).first()
        if not selected_period:
            return HttpResponse("Invalid period. Please select a processed payroll period.", status=400)

        # -----------------------------
        # Fetch current results (scoped)
        # -----------------------------
        results = PayrollResult.objects.select_related("employee", "period", "period__payroll")

        if company:
            results = results.filter(period__payroll__company=company)
        if country:
            results = results.filter(period__payroll__country=country)

        results = results.filter(period_id=selected_period.id)

        # -----------------------------
        # Label preference
        # -----------------------------
        prefer_label = "description"
        if isinstance(settings, dict):
            pref = (settings.get("payslip_label_preference") or "").strip().lower()
            if pref in {"name", "description"}:
                prefer_label = pref

        # -----------------------------
        # Resolve previous period (scoped) + previous results
        # -----------------------------
        prev_period = None

        if getattr(selected_period, "payment_date", None):
            prev_period = (
                processed_periods.filter(payment_date__lt=selected_period.payment_date)
                .order_by("-payment_date", "-id")
                .first()
            )

        if prev_period is None:
            prev_period = (
                processed_periods.filter(id__lt=selected_period.id)
                .order_by("-id")
                .first()
            )

        prev_results = PayrollResult.objects.select_related("employee", "period", "period__payroll")

        if company:
            prev_results = prev_results.filter(period__payroll__company=company)
        if country:
            prev_results = prev_results.filter(period__payroll__country=country)

        prev_results = prev_results.filter(period_id=prev_period.id) if prev_period else prev_results.none()

        # -----------------------------
        # Build context + render HTML
        # -----------------------------
        payslips = build_payslips(
            results,
            country=country,
            company=company,
            prefer_label=prefer_label,
        )

        context = {
            "company": company,
            "country": country,
            "results": results,
            "payslips": payslips,
            "period": selected_period,
            "processed_periods": processed_periods,
            "selected_period_id": str(selected_period.id),
            "base_url": request.build_absolute_uri("/").rstrip("/"),
            "company_logo_url": None,
            "settings": settings,
            "user": request.user,
        }

        rendered_html = ReportEngine.render_report(config, context)

        # -----------------------------
        # Exports
        # -----------------------------
        if export_format == "pdf":
            try:
                pdf_file = render_to_pdf(rendered_html, base_url=context["base_url"])
                response = HttpResponse(pdf_file, content_type="application/pdf")
                response["Content-Disposition"] = f'inline; filename="{report_code}.pdf"'
                return response
            except Exception as e:
                return HttpResponse(f"PDF export failed: {e}", status=500, content_type="text/plain")

        if export_format == "csv":
            if report_mode == "comparison_gross_to_net":
                comparison_rows = build_gross_to_net_comparison_rows(
                    current_results=results,
                    previous_results=prev_results,
                    current_period=selected_period,
                    previous_period=prev_period,
                    country=country,
                    company=company,
                )
                comparison_fields = [
                    "Company_id",
                    "Id",
                    "Period",
                    "Employee",
                    "Code",
                    "Description",
                    "Current Period",
                    "Previous Period",
                    "Balance",
                ]
                csv_data = render_to_csv(comparison_rows, field_list=comparison_fields)
                response = HttpResponse(csv_data, content_type="text/csv")
                response["Content-Disposition"] = f'attachment; filename="{report_code}.csv"'
                return response

            fallback_fields = ["employee", "gross_pay", "total_deductions", "total_tax", "net_pay", "details"]
            csv_data = render_to_csv(results, field_list=fallback_fields)
            response = HttpResponse(csv_data, content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="{report_code}.csv"'
            return response

        # Default HTML
        return HttpResponse(rendered_html)
    


