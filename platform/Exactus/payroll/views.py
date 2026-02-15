import logging
import json
import csv
import io
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import Sum, Count, Q
from django.utils.decorators import method_decorator
from django.db import transaction

# --- MODELS ---
from Exactus.company.models import Company
from Exactus.country.models import Country
from Exactus.employee.models import Employee
from Exactus.pdcodes.models import PDcode
from Exactus.payroll.models import (
    Payroll, PayrollPeriod, PayrollExecutionLog, 
    PeriodStatus, PayrollResult
)
from Exactus.compensation.models import CompensationComponent
from Exactus.country.utils.decorators import role_required

# --- OPTIONAL MODELS (Safety Checks) ---
try:
    from Exactus.elements.models import Element
except ImportError:
    Element = None

try:
    from Exactus.calculationbase.models import CalculationBase
except ImportError:
    CalculationBase = None

# --- FORMS ---
from .forms import (
    PayrollForm, 
    PayrollPeriodForm, 
    PayrollProcessForm, 
    HistoricalUploadForm
)

# --- CALCULATOR ---
try:
    from Exactus.payroll.calculator.universal import UniversalPayrollCalculator
except ImportError:
    UniversalPayrollCalculator = None

logger = logging.getLogger(__name__)

# ============================================================
# PAYROLL DASHBOARD
# ============================================================

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def payroll_dashboard(request, country_slug, company_id):
    company = get_object_or_404(Company, pk=company_id)
    country = get_object_or_404(Country, slug=country_slug)
    
    active_payrolls = Payroll.objects.filter(
        company=company
    ).order_by('-fiscal_year')
    
    recent_periods = PayrollPeriod.objects.filter(
        payroll__company=company
    ).order_by('-created_at')[:10]
    
    total_payrolls = active_payrolls.count()
    total_periods = PayrollPeriod.objects.filter(payroll__company=company).count()
    
    total_amount = PayrollPeriod.objects.filter(
        payroll__company=company,
        status=PeriodStatus.COMPLETED
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'company': company,
        'country': country,
        'company_id': company_id,
        'country_slug': country_slug,
        'active_payrolls': active_payrolls,
        'recent_periods': recent_periods,
        'total_payrolls': total_payrolls,
        'total_periods': total_periods,
        'total_amount': total_amount,
    }
    return render(request, 'payroll/payroll_dashboard.html', context)


# ============================================================
# PAYROLL LIST
# ============================================================

@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE"), name='dispatch')
class PayrollListView(LoginRequiredMixin, ListView):
    model = Payroll
    template_name = "payroll/payroll_list.html"
    context_object_name = "payrolls"
    paginate_by = 20

    def get_queryset(self):
        company_id = self.kwargs["company_id"]
        queryset = Payroll.objects.filter(company_id=company_id).order_by("-fiscal_year")
        return queryset.annotate(
            period_count=Count('periods'),
            total_amount_sum=Sum('periods__total_amount')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs["company_id"]
        country_slug = self.kwargs["country_slug"]
        context["company"] = get_object_or_404(Company, pk=company_id)
        context["country"] = get_object_or_404(Country, slug=country_slug)
        context["company_id"] = company_id
        context["country_slug"] = country_slug
        return context


# ============================================================
# PAYROLL DETAIL
# ============================================================

@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE"), name='dispatch')
class PayrollDetailView(LoginRequiredMixin, DetailView):
    model = Payroll
    template_name = "payroll/payroll_detail.html"
    context_object_name = "payroll"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payroll = self.get_object()
        periods = payroll.periods.all().order_by("period_number")
        
        total_amount = periods.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_employees = periods.aggregate(total=Sum('employee_count'))['total'] or 0

        summary = {
            'total_periods': periods.count(),
            'pending_periods': periods.filter(status=PeriodStatus.PENDING).count(),
            'completed_periods': periods.filter(status=PeriodStatus.COMPLETED).count(),
            'locked_periods': periods.filter(status=PeriodStatus.LOCKED).count(),
            'total_amount': total_amount,
            'total_employees': total_employees,
        }
        
        context["periods"] = periods
        context["summary"] = summary
        context["country_slug"] = self.kwargs["country_slug"]
        context["company_id"] = self.kwargs["company_id"]
        return context


# ============================================================
# PAYROLL CREATE / UPDATE / DELETE
# ============================================================

@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE"), name='dispatch')
class PayrollCreateView(LoginRequiredMixin, CreateView):
    model = Payroll
    form_class = PayrollForm
    template_name = "payroll/payroll_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company"] = get_object_or_404(Company, pk=self.kwargs["company_id"])
        context["country"] = get_object_or_404(Country, slug=self.kwargs["country_slug"])
        context["company_id"] = self.kwargs["company_id"]
        context["country_slug"] = self.kwargs["country_slug"]
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['country'] = get_object_or_404(Country, slug=self.kwargs["country_slug"])
        kwargs['company'] = get_object_or_404(Company, pk=self.kwargs["company_id"])
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "payroll:payroll_detail",
            kwargs={
                "country_slug": self.kwargs["country_slug"],
                "company_id": self.kwargs["company_id"],
                "pk": self.object.pk,
            },
        )

@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST",), name='dispatch')
class PayrollUpdateView(LoginRequiredMixin, UpdateView):
    model = Payroll
    template_name = "payroll/payroll_form.html"
    form_class = PayrollForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['country'] = self.object.country
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_id"] = self.kwargs["company_id"]
        context["country_slug"] = self.kwargs["country_slug"]
        return context

    def get_success_url(self):
        return reverse_lazy(
            "payroll:payroll_detail",
            kwargs={
                "country_slug": self.kwargs["country_slug"],
                "company_id": self.kwargs["company_id"],
                "pk": self.object.pk,
            },
        )

@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST",), name='dispatch')
class PayrollDeleteView(LoginRequiredMixin, DeleteView):
    model = Payroll
    template_name = "payroll/payroll_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_id"] = self.kwargs["company_id"]
        context["country_slug"] = self.kwargs["country_slug"]
        return context

    def delete(self, request, *args, **kwargs):
        payroll = self.get_object()
        payroll.delete()
        messages.success(request, f"Payroll FY{payroll.fiscal_year} has been deleted.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy(
            "payroll:payroll_list",
            kwargs={
                "country_slug": self.kwargs["country_slug"],
                "company_id": self.kwargs["company_id"],
                "pk": self.object.pk,
            },
        )


# ============================================================
# PERIOD LIST
# ============================================================

@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE"), name='dispatch')
class PayrollPeriodListView(LoginRequiredMixin, ListView):
    model = PayrollPeriod
    template_name = "payroll/period_list.html"
    context_object_name = "periods"
    paginate_by = 20

    def get_queryset(self):
        payroll_id = self.kwargs["payroll_id"]
        return PayrollPeriod.objects.filter(payroll_id=payroll_id).order_by("period_number")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payroll_id = self.kwargs["payroll_id"]
        context["payroll"] = get_object_or_404(Payroll, pk=payroll_id)
        context["company_id"] = self.kwargs["company_id"]
        context["country_slug"] = self.kwargs["country_slug"]
        context["payroll_id"] = payroll_id
        return context


# ============================================================
# PERIOD DETAIL VIEW (UPDATED VISIBILITY LOGIC)
# ============================================================

import json
import logging
from decimal import Decimal
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

from Exactus.payroll.models import PayrollPeriod, PeriodStatus
from Exactus.employee.models import Employee
from Exactus.pdcodes.models import PDcode

try:
    from Exactus.elements.models import Element
except ImportError:
    Element = None

try:
    from Exactus.payroll.calculator.universal import UniversalPayrollCalculator
except ImportError:
    UniversalPayrollCalculator = None

logger = logging.getLogger(__name__)


class PayrollPeriodDetailView(LoginRequiredMixin, DetailView):
    model = PayrollPeriod
    template_name = "payroll/period_detail.html"
    context_object_name = "period"

    SYSTEM_LABELS = {
        "5000": "Gross Pay",
        "6000": "Income Tax",
        "7000": "National Insurance",
        "8000": "Net Salary",
        "9000": "Employer Cost",
    }

    ALWAYS_VISIBLE_CODES = {"5000", "6000", "7000", "8000", "9000"}

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    def _parse_details(self, details_data):
        if isinstance(details_data, str):
            try:
                return json.loads(details_data)
            except json.JSONDecodeError:
                return {}
        return details_data if isinstance(details_data, dict) else {}

    def _to_decimal(self, v) -> Decimal:
        try:
            return Decimal(str(v))
        except Exception:
            return Decimal("0.00")

    def _to_float(self, v) -> float:
        try:
            return float(v)
        except Exception:
            return 0.0

    def _norm(self, s: str) -> str:
        return (s or "").strip().lower()

    def _is_gross_header(self, h: dict) -> bool:
        code = self._norm(str(h.get("code", "")))
        label = self._norm(h.get("label", ""))
        # Prefer code match
        if code == "5000":
            return True
        # Label match
        return ("gross pay" in label) or ("gross salary" in label) or (label == "gross")

    def _is_net_header(self, h: dict) -> bool:
        code = self._norm(str(h.get("code", "")))
        label = self._norm(h.get("label", ""))
        if code == "8000":
            return True
        return ("net salary" in label) or ("net pay" in label) or ("take home" in label) or (label == "net")

    def _build_config_maps(self, period, company_id):
        elem_config = {}
        pd_config = {}

        # Elements
        try:
            if Element:
                qs = Element.objects.filter(country=period.payroll.country)
                for el in qs:
                    elem_config[str(el.element_code)] = {
                        "name": el.element_name,
                        "status": el.element_status,
                    }
        except Exception:
            pass

        # PD Codes
        try:
            qs = PDcode.objects.filter(company_id=company_id)
            for pd in qs:
                pd_config[str(pd.pdcode_code)] = {
                    "name": pd.pdcode_name,
                    "status": pd.pdcode_status,
                }
        except Exception:
            pass

        return elem_config, pd_config

    def _is_visible_code(self, code: str, value: float, elem_config: dict, pd_config: dict) -> bool:
        # must exist
        if abs(value) <= 0.001:
            return False

        # Rule 1: System totals always visible
        if code in self.ALWAYS_VISIBLE_CODES:
            return True

        # Rule 2: Configured items (Visible)
        if code in pd_config:
            return pd_config[code].get("status") == "Visible"
        if code in elem_config:
            return elem_config[code].get("status") == "Visible"

        # Rule 3: Unconfigured fallback ranges
        if code.isdigit():
            c = int(code)
            if (1000 <= c <= 4999) or (6000 <= c <= 6999) or (7000 <= c <= 7999) or (9000 <= c <= 9999):
                return True

        return False

    def _label_for_code(self, code: str, elem_config: dict, pd_config: dict) -> str:
        if code in self.SYSTEM_LABELS:
            return self.SYSTEM_LABELS[code]
        if code in elem_config:
            return elem_config[code].get("name") or f"Code {code}"
        if code in pd_config:
            return pd_config[code].get("name") or f"Code {code}"
        return f"Code {code}"

    def _sort_key(self, code: str):
        try:
            return int(code)
        except Exception:
            return 999999

    def _compute_kpis(self, final_headers: list[dict], grand_totals: list[Decimal]):
        """
        REQUIRED RULES:
        - Total Gross = total of the Gross Pay/Gross Salary column (or code 5000)
        - Net Pay     = total of the Net Salary/Net Pay column (or code 8000)
        - Deductions  = sum of ALL columns between Gross and Net (exclusive)
        """
        gross_idx = next((i for i, h in enumerate(final_headers) if self._is_gross_header(h)), None)
        net_idx = next((i for i, h in enumerate(final_headers) if self._is_net_header(h)), None)

        kpi_gross = Decimal("0.00")
        kpi_net = Decimal("0.00")
        kpi_deductions = Decimal("0.00")

        if gross_idx is None or net_idx is None:
            return {
                "gross": kpi_gross,
                "deductions": kpi_deductions,
                "net": kpi_net,
                "gross_idx": gross_idx,
                "net_idx": net_idx,
            }

        left = min(gross_idx, net_idx)
        right = max(gross_idx, net_idx)

        try:
            kpi_gross = self._to_decimal(grand_totals[gross_idx])
        except Exception:
            pass

        try:
            kpi_net = self._to_decimal(grand_totals[net_idx])
        except Exception:
            pass

        for j in range(left + 1, right):
            try:
                kpi_deductions += self._to_decimal(grand_totals[j])
            except Exception:
                pass

        # Show deductions as positive (template prints the minus sign)
        kpi_deductions = abs(kpi_deductions)

        return {
            "gross": kpi_gross,
            "deductions": kpi_deductions,
            "net": kpi_net,
            "gross_idx": gross_idx,
            "net_idx": net_idx,
        }

    # ------------------------------------------------------------
    # Main
    # ------------------------------------------------------------
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period: PayrollPeriod = self.object
        company_id = self.kwargs.get("company_id")

        eligible_employees = period.get_eligible_employees()

        use_stored_results = period.status in [
            PeriodStatus.PROCESSED,
            PeriodStatus.AWAITING_APPROVAL,
            PeriodStatus.COMPLETED,
            PeriodStatus.LOCKED,
        ]

        elem_config, pd_config = self._build_config_maps(period, company_id)

        # Decide loop target
        if use_stored_results:
            loop_target = period.results.select_related("employee").all()
            if not loop_target.exists():
                loop_target = eligible_employees
                use_stored_results = False
        else:
            loop_target = eligible_employees

        report_rows = []
        active_codes = set()

        for obj in loop_target:
            if hasattr(obj, "employee"):
                emp = obj.employee
                stored_result = obj
            else:
                emp = obj
                stored_result = None

            row_data = {}

            # -------- A) Stored results (DB) --------
            if use_stored_results and stored_result:
                details = self._parse_details(stored_result.details)

                # New structured format
                if isinstance(details, dict) and "elements" in details:
                    for k, v in (details.get("elements") or {}).items():
                        row_data[str(k)] = self._to_float(v)

                    for item in (details.get("pd_codes") or []):
                        code = str(item.get("code"))
                        row_data[code] = self._to_float(item.get("amount"))

                # Old flat format fallback
                else:
                    for k, v in (details or {}).items():
                        kk = str(k)
                        if kk == "Gross Pay":
                            kk = "5000"
                        if kk in ("Net Salary", "Net Pay"):
                            kk = "8000"
                        row_data[kk] = self._to_float(v)

            # -------- B) Live preview --------
            else:
                if UniversalPayrollCalculator:
                    try:
                        calc = UniversalPayrollCalculator(period=period, employee=emp)
                        res = calc.calculate()

                        for k, v in (res.get("elements") or {}).items():
                            row_data[str(k)] = self._to_float(v)

                        for item in (res.get("pd_codes") or []):
                            row_data[str(item.get("code"))] = self._to_float(item.get("amount"))

                    except Exception as e:
                        logger.error(f"Preview Error for {emp}: {e}")

            # Determine visible columns and collect active codes
            for code, val in row_data.items():
                if self._is_visible_code(code, val, elem_config, pd_config):
                    active_codes.add(code)

            report_rows.append({"employee": emp, "data": row_data})

        # Build final headers
        sorted_codes = sorted(active_codes, key=self._sort_key)
        final_headers = [{"code": c, "label": self._label_for_code(c, elem_config, pd_config)} for c in sorted_codes]

        # Build table rows + grand totals
        table_rows = []
        grand_totals = [Decimal("0.00")] * len(final_headers)

        for item in report_rows:
            emp = item["employee"]
            data = item["data"]

            cells = []
            for idx, h in enumerate(final_headers):
                v = data.get(h["code"], 0.0)
                cells.append(v)
                grand_totals[idx] += self._to_decimal(v)

            table_rows.append(
                {
                    "employee_name": f"{emp.employee_name} {emp.employee_surname}",
                    "employee_id": getattr(emp, "employee_id", emp.id),
                    "cells": cells,
                }
            )

        # KPI totals (meaning-based, order-independent)
        kpis = self._compute_kpis(final_headers, grand_totals)

        # Approver permission
        user = self.request.user
        allowed_approvers = [
            "EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION",
            "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE"
        ]
        can_approve = False
        if getattr(user, "is_superuser", False):
            can_approve = True
        elif hasattr(user, "roles"):
            can_approve = user.roles.filter(name__in=allowed_approvers).exists()
        elif hasattr(user, "role"):
            can_approve = str(user.role).upper() in allowed_approvers

        context.update(
            {
                "headers": final_headers,
                "rows": table_rows,

                # keep totals if you still want them for debugging
                "totals": grand_totals,

                # ✅ NEW: KPI dict used by template
                "kpis": kpis,

                "company_id": company_id,
                "country_slug": self.kwargs["country_slug"],
                "payroll_id": self.kwargs["payroll_id"],

                "can_process": period.status == PeriodStatus.PENDING,
                "can_reset": period.status == PeriodStatus.PROCESSED,
                "can_send_approval": period.status == PeriodStatus.PROCESSED,

                "can_reject": period.status == PeriodStatus.AWAITING_APPROVAL and can_approve,
                "can_authorize": period.status == PeriodStatus.AWAITING_APPROVAL and can_approve,

                "is_locked": period.status in [PeriodStatus.COMPLETED, PeriodStatus.LOCKED],
            }
        )
        return context

# ============================================================
# PAYROLL PROCESS VIEW
# ============================================================

@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION"), name='dispatch')
class PayrollPeriodProcessView(LoginRequiredMixin, View):
    """View to trigger the calculation (Process Button)."""
    
    def post(self, request, *args, **kwargs):
        period_id = kwargs.get('period_id') or kwargs.get('pk')
        period = get_object_or_404(PayrollPeriod, pk=period_id)
        
        if period.status != PeriodStatus.PENDING:
             return JsonResponse({'success': False, 'error': "Period is not in Pending status."}, status=400)
             
        eligible_employees = period.get_eligible_employees()
        
        period_total_gross = Decimal('0.00')
        period_total_net = Decimal('0.00')
        period_total_tax = Decimal('0.00')
        processed_count = 0
        
        try:
            with transaction.atomic():
                period.results.all().delete()
                
                if not UniversalPayrollCalculator:
                     return JsonResponse({'success': False, 'error': "Calculator engine not found."}, status=500)

                for emp in eligible_employees:
                    try:
                        calc = UniversalPayrollCalculator(period=period, employee=emp)
                        res = calc.calculate()
                        
                        elements = res.get('elements', {})
                        gross = Decimal(str(elements.get('5000', 0)))
                        net = Decimal(str(elements.get('8000', 0)))
                        tax_val = abs(Decimal(str(elements.get('6000', 0))))
                        total_deductions = gross - net

                        details_payload = {
                            'elements': elements,
                            'pd_codes': res.get('pd_codes', []),
                            'breakdown': res.get('breakdown', [])
                        }

                        PayrollResult.objects.create(
                            period=period,
                            employee=emp,
                            gross_pay=gross,
                            net_pay=net,
                            total_tax=tax_val, 
                            total_deductions=total_deductions,
                            details=json.dumps(details_payload, default=str)
                        )
                        
                        period_total_gross += gross
                        period_total_net += net
                        period_total_tax += tax_val
                        processed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to process {emp}: {e}")
                
                if processed_count > 0:
                    period.total_gross = period_total_gross
                    period.total_net = period_total_net
                    period.total_tax = period_total_tax
                    period.total_amount = period_total_net
                    period.employee_count = processed_count
                    period.status = PeriodStatus.PROCESSED
                    period.save()
                    
                    messages.success(request, f"Successfully processed {processed_count} employees.")
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': "No employees were processed."})
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': f"Processing Error: {str(e)}"}, status=500)


# ============================================================
# PERIOD CREATE, UPDATE, DELETE
# ============================================================

@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST"), name='dispatch')
class PayrollPeriodCreateView(LoginRequiredMixin, CreateView):
    model = PayrollPeriod
    form_class = PayrollPeriodForm
    template_name = "payroll/period_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.payroll = get_object_or_404(Payroll, pk=self.kwargs["payroll_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['payroll'] = self.payroll
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial['payroll'] = self.payroll
        today = timezone.now().date()
        last_period = PayrollPeriod.objects.filter(payroll=self.payroll).order_by('end_date').last()
        
        if last_period:
            initial['start_date'] = last_period.end_date + timezone.timedelta(days=1)
            initial['end_date'] = last_period.end_date + timezone.timedelta(days=30)
        else:
            initial['start_date'] = today.replace(day=1)
            import calendar
            last_day = calendar.monthrange(today.year, today.month)[1]
            initial['end_date'] = today.replace(day=last_day)
        
        if initial.get('end_date'):
            initial['processing_date'] = initial['end_date'] + timezone.timedelta(days=5)
            initial['payment_date'] = initial['end_date'] + timezone.timedelta(days=7)
        return initial

    def form_valid(self, form):
        form.instance.payroll = self.payroll
        form.instance.created_by = self.request.user
        if not form.instance.name and form.instance.start_date:
            form.instance.name = form.instance.start_date.strftime('%B %Y')
        try:
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payroll"] = self.payroll
        context["company_id"] = self.kwargs["company_id"]
        context["country_slug"] = self.kwargs["country_slug"]
        context["payroll_id"] = self.kwargs["payroll_id"]
        return context

    def get_success_url(self):
        if self.payroll.is_historical:
            return reverse_lazy(
                "payroll:historical_upload",
                kwargs={
                    "country_slug": self.kwargs["country_slug"],
                    "company_id": self.kwargs["company_id"],
                    "payroll_id": self.kwargs["payroll_id"],
                    "period_id": self.object.pk,
                }
            )
        return reverse_lazy("payroll:period_detail", kwargs={
            "country_slug": self.kwargs["country_slug"],
            "company_id": self.kwargs["company_id"],
            "payroll_id": self.kwargs["payroll_id"],
            "pk": self.object.pk,
        })


@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST"), name='dispatch')
class PayrollPeriodUpdateView(LoginRequiredMixin, UpdateView):
    model = PayrollPeriod
    form_class = PayrollPeriodForm
    template_name = "payroll/period_form.html"

    def dispatch(self, request, *args, **kwargs):
        period = self.get_object()
        if not period.is_editable:
            messages.error(request, f"Cannot edit period with status: {period.get_status_display()}")
            return redirect("payroll:period_detail", country_slug=self.kwargs["country_slug"], company_id=self.kwargs["company_id"], payroll_id=self.kwargs["payroll_id"], pk=period.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['payroll'] = self.object.payroll
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_id"] = self.kwargs["company_id"]
        context["country_slug"] = self.kwargs["country_slug"]
        context["payroll_id"] = self.kwargs["payroll_id"]
        return context

    def get_success_url(self):
        return reverse_lazy("payroll:period_detail", kwargs={
            "country_slug": self.kwargs["country_slug"],
            "company_id": self.kwargs["company_id"],
            "payroll_id": self.kwargs["payroll_id"],
            "pk": self.object.pk,
        })


@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST"), name='dispatch')
class PayrollPeriodDeleteView(LoginRequiredMixin, DeleteView):
    model = PayrollPeriod
    template_name = "payroll/period_confirm_delete.html"

    def dispatch(self, request, *args, **kwargs):
        period = self.get_object()
        if not period.is_deletable:
            messages.error(request, f"Cannot delete period with status: {period.get_status_display()}")
            return redirect("payroll:period_detail", country_slug=self.kwargs["country_slug"], company_id=self.kwargs["company_id"], payroll_id=self.kwargs["payroll_id"], pk=period.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_id"] = self.kwargs["company_id"]
        context["country_slug"] = self.kwargs["country_slug"]
        context["payroll_id"] = self.kwargs["payroll_id"]
        return context

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Period deleted successfully.")
        return response

    def get_success_url(self):
        return reverse_lazy("payroll:period_list", kwargs={
            "country_slug": self.kwargs["country_slug"],
            "company_id": self.kwargs["company_id"],
            "payroll_id": self.kwargs["payroll_id"],
        })


# ============================================================
# WORKFLOW ACTIONS (SEND, APPROVE, REJECT)
# ============================================================

@method_decorator(login_required, name="dispatch")
@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST"), name='dispatch')
class PayrollPeriodSendApprovalView(View):
    def post(self, request, country_slug, company_id, payroll_id, period_id):
        try:
            period = get_object_or_404(PayrollPeriod, pk=period_id, payroll_id=payroll_id)
            if period.status != PeriodStatus.PROCESSED:
                 return JsonResponse({"success": False, "error": "Period must be processed before sending for approval."}, status=400)
            period.send_for_approval()
            messages.success(request, f"Period {period.name} sent for approval.")
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


@method_decorator(login_required, name="dispatch")
@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER"), name='dispatch')
class PayrollPeriodAuthorizeView(View):
    def post(self, request, country_slug, company_id, payroll_id, period_id):
        try:
            allowed_roles = ["EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE"]
            user = request.user
            has_permission = False
            if user.is_superuser:
                has_permission = True
            elif hasattr(user, 'roles'):
                has_permission = user.roles.filter(name__in=allowed_roles).exists()
            elif hasattr(user, 'role'):
                role_str = str(user.role).upper()
                has_permission = role_str in allowed_roles
            
            if not has_permission:
                 return JsonResponse({"success": False, "error": "Permission Denied."}, status=403)

            period = get_object_or_404(PayrollPeriod, pk=period_id, payroll_id=payroll_id)
            if period.status != PeriodStatus.AWAITING_APPROVAL:
                 return JsonResponse({"success": False, "error": "Period is not awaiting approval."}, status=400)
                 
            period.authorize(request.user)
            PayrollExecutionLog.objects.create(period=period, execution_type="approval", status="completed", input_data={"action": "authorize"}, executed_by=request.user)
            messages.success(request, f"Period {period.name} authorized and completed.")
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Authorization Failed: {str(e)}"}, status=500)


@method_decorator(login_required, name="dispatch")
@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER"), name='dispatch')
class PayrollPeriodRejectView(View):
    def post(self, request, country_slug, company_id, payroll_id, period_id):
        try:
            allowed_roles = ["EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE"]
            user = request.user
            has_permission = False
            if user.is_superuser:
                has_permission = True
            elif hasattr(user, 'roles'):
                has_permission = user.roles.filter(name__in=allowed_roles).exists()
            elif hasattr(user, 'role'):
                role_str = str(user.role).upper()
                has_permission = role_str in allowed_roles
            
            if not has_permission:
                 return JsonResponse({"success": False, "error": "Permission Denied."}, status=403)

            period = get_object_or_404(PayrollPeriod, pk=period_id, payroll_id=payroll_id)
            if period.status != PeriodStatus.AWAITING_APPROVAL:
                 return JsonResponse({"success": False, "error": "Period is not awaiting approval."}, status=400)
            
            with transaction.atomic():
                PayrollResult.objects.filter(period=period).delete()
                CompensationComponent.objects.filter(processed=True, processed_period=period.name).update(processed=False, processed_period='')
                period.reject()
                PayrollExecutionLog.objects.create(period=period, execution_type="approval", status="cancelled", input_data={"action": "reject"}, executed_by=request.user)

            messages.warning(request, f"Period {period.name} rejected.")
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Rejection Failed: {str(e)}"}, status=500)


# ============================================================
# EXPORT & RESET UTILS
# ============================================================

@method_decorator(login_required, name='dispatch')
@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE"), name='dispatch')
class PayrollPeriodExportView(View):
    def get(self, request, country_slug, company_id, payroll_id, period_id):
        period = get_object_or_404(PayrollPeriod, pk=period_id)
        results = PayrollResult.objects.filter(period=period).select_related('employee')
        
        # 1. CONFIGURATION
        elem_config = {}
        try:
            if Element:
                all_elems = Element.objects.filter(country=period.payroll.country)
                for el in all_elems:
                    elem_config[str(el.element_code)] = {'name': el.element_name, 'status': el.element_status}
        except: pass

        pd_config = {}
        try:
            all_pds = PDcode.objects.filter(company_id=company_id)
            for pd in all_pds:
                pd_config[str(pd.pdcode_code)] = {'name': pd.pdcode_name, 'status': pd.pdcode_status}
        except: pass

        rows_data = []
        active_codes = set()

        for res in results:
            details = res.details
            if isinstance(details, str):
                try: details = json.loads(details)
                except: details = {}
            elif not isinstance(details, dict): details = {}

            data_to_scan = details
            if 'elements' in details:
                data_to_scan = details.get('elements', {})
                pd_list = details.get('pd_codes', [])
                for p in pd_list:
                    data_to_scan[str(p.get('code'))] = p.get('amount')

            for k, v in data_to_scan.items():
                try:
                    val = float(v)
                    if abs(val) > 0.001:
                        is_visible = False
                        
                        # Rule 1: System Totals (Always Show)
                        if k in ['5000', '6000', '7000', '8000', '9000']:
                            is_visible = True
                        
                        # Rule 2: Configured Items (Check Status)
                        elif k in pd_config:
                            if pd_config[k]['status'] == 'Visible': is_visible = True
                        elif k in elem_config:
                            if elem_config[k]['status'] == 'Visible': is_visible = True
                        
                        # Rule 3: Unconfigured Fallback (Ranges)
                        elif k.isdigit():
                            c = int(k)
                            if (1000 <= c <= 4999) or (6000 <= c <= 6999) or (7000 <= c <= 7999) or (9000 <= c <= 9999):
                                is_visible = True
                        
                        if is_visible:
                            active_codes.add(k)
                except: pass
            
            rows_data.append({'employee': res.employee, 'data': data_to_scan})

        def strict_numerical_sort(val):
            try: return int(val)
            except: return 999999
            
        sorted_codes = sorted(list(active_codes), key=strict_numerical_sort)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="Report_{period.name}.csv"'
        writer = csv.writer(response)
        
        writer.writerow([f"Gross to Net Report: {period.name}"])
        writer.writerow([]) 
        
        system_labels = {
            '5000': 'Gross Pay', '6000': 'Income Tax', '7000': 'National Insurance',
            '8000': 'Net Salary', '9000': 'Employer Cost'
        }
        
        csv_headers = ['Employee ID', 'Employee Name']
        csv_codes = ['', '']
        
        for c in sorted_codes:
            name = f"Code {c}"
            if c in system_labels: name = system_labels[c]
            elif c in elem_config: name = elem_config[c]['name']
            elif c in pd_config: name = pd_config[c]['name']
            csv_headers.append(name)
            csv_codes.append(str(c))

        writer.writerow(csv_headers)
        writer.writerow(csv_codes)
        
        col_totals = {code: Decimal('0.00') for code in sorted_codes}

        for item in rows_data:
            emp = item['employee']
            details = item['data']
            row = [getattr(emp, 'employee_id', ''), f"{emp.employee_name} {emp.employee_surname}"]
            for code in sorted_codes:
                val = details.get(code, 0.0)
                try:
                    val = float(val)
                    if 6000 <= int(code) <= 7999: val = abs(val)
                except: val = 0.0
                col_totals[code] += Decimal(str(val))
                row.append(f"{val:.2f}")
            writer.writerow(row)

        totals_row = ['', 'TOTALS']
        for code in sorted_codes:
            totals_row.append(f"{col_totals[code]:.2f}")
        writer.writerow(totals_row)
            
        return response


@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST") , name='dispatch')
@require_http_methods(["GET", "POST"])
def payroll_reset_confirm(request, country_slug, company_id, payroll_id):
    payroll = get_object_or_404(Payroll, pk=payroll_id, company_id=company_id)
    if request.method == "POST":
        try:
            with transaction.atomic():
                PayrollPeriod.objects.filter(payroll=payroll).update(status=PeriodStatus.PENDING, total_gross=0, total_net=0, total_tax=0, total_amount=0)
                PayrollResult.objects.filter(period__payroll=payroll).delete()
                messages.success(request, f"Successfully reset Payroll FY{payroll.fiscal_year}.")
                return redirect('payroll:payroll_detail', country_slug=country_slug, company_id=company_id, pk=payroll.pk)
        except Exception as e:
            messages.error(request, f"Error: {e}")
    context = {'payroll': payroll, 'company_id': company_id, 'country_slug': country_slug}
    return render(request, 'payroll/payroll_reset_confirm.html', context)


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
@require_POST
def reset_payroll(request, country_slug, company_id, payroll_id):
    payroll = get_object_or_404(Payroll, pk=payroll_id, company_id=company_id)
    try:
        with transaction.atomic():
            PayrollPeriod.objects.filter(payroll=payroll).update(status=PeriodStatus.PENDING, total_gross=0, total_net=0, total_tax=0)
            PayrollResult.objects.filter(period__payroll=payroll).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
@require_http_methods(["GET", "POST"])
def payroll_period_reset_confirm(request, country_slug, company_id, payroll_id, period_id):
    period = get_object_or_404(PayrollPeriod, pk=period_id, payroll_id=payroll_id)
    if request.method == "POST":
        try:
            with transaction.atomic():
                PayrollResult.objects.filter(period=period).delete()
                CompensationComponent.objects.filter(processed=True, processed_period=period.name).update(processed=False, processed_period='')
                period.status = PeriodStatus.PENDING
                period.total_gross = 0
                period.total_net = 0
                period.total_tax = 0
                period.total_amount = 0
                period.save()
                messages.success(request, f"Period {period.name} reset.")
                return redirect('payroll:period_detail', country_slug=country_slug, company_id=company_id, payroll_id=payroll_id, pk=period.pk)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, 'payroll/period_reset_confirm.html', {'period': period, 'country_slug': country_slug, 'company_id': company_id})


# ============================================================
# HISTORICAL UPLOAD
# ============================================================

@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST",), name='dispatch')
class PayrollHistoricalUploadView(LoginRequiredMixin, View):
    def get(self, request, country_slug, company_id, payroll_id, period_id):
        period = get_object_or_404(PayrollPeriod, pk=period_id, payroll__is_historical=True)
        form = HistoricalUploadForm()
        context = {'form': form, 'period': period, 'company_id': company_id, 'country_slug': country_slug, 'payroll_id': payroll_id}
        return render(request, 'payroll/historical_upload.html', context)

    def post(self, request, country_slug, company_id, payroll_id, period_id):
        period = get_object_or_404(PayrollPeriod, pk=period_id, payroll__is_historical=True)
        form = HistoricalUploadForm(request.POST, request.FILES)
        context = {'form': form, 'period': period, 'company_id': company_id, 'country_slug': country_slug, 'payroll_id': payroll_id}

        if not form.is_valid():
            return render(request, 'payroll/historical_upload.html', context)

        file = request.FILES['file']
        try:
            decoded_file = file.read().decode('utf-8-sig')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            headers = reader.fieldnames or []
        except Exception as e:
            messages.error(request, f"Error reading CSV: {e}")
            return render(request, 'payroll/historical_upload.html', context)
        
        company = get_object_or_404(Company, pk=company_id)
        country = get_object_or_404(Country, slug=country_slug)
        db_elements = set(Element.objects.filter(country=country).values_list('element_code', flat=True)) if Element else set()
        db_pdcodes = set(PDcode.objects.filter(company=company).values_list('pdcode_code', flat=True))
        ignored_cols = ['Employee ID', 'Employee Code', 'Employee Name', 'Name', 'Surname', 'Gross Pay', 'Net Salary', 'Total Tax', 'Total Deductions', 'Net Pay']
        missing_codes = []
        
        for header in headers:
            clean_header = header.strip()
            if clean_header in ignored_cols: continue
            if clean_header not in db_elements and clean_header not in db_pdcodes:
                missing_codes.append(clean_header)

        if missing_codes:
            return render(request, 'payroll/historical_upload_result.html', {'success': False, 'missing_codes': missing_codes, 'period': period, 'company_id': company_id, 'country_slug': country_slug, 'payroll_id': payroll_id})

        try:
            with transaction.atomic():
                period.status = PeriodStatus.PROCESSING
                period.processed_by = request.user
                period.processed_at = timezone.now()
                period.save()
                PayrollResult.objects.filter(period=period).delete()
                
                results_to_create = []
                row_count = 0
                total_gross_sum = Decimal(0)
                total_net_sum = Decimal(0)
                total_tax_sum = Decimal(0)

                io_string.seek(0)
                reader = csv.DictReader(io_string)

                for row in reader:
                    emp_id = row.get('Employee ID') or row.get('Employee Code')
                    if not emp_id: continue
                    emp = Employee.objects.filter(company_id=company_id, employee_id=emp_id).first()
                    if not emp: emp = Employee.objects.filter(company_id=company_id, employee_code=emp_id).first()
                    if not emp: continue

                    details = {}
                    gross = Decimal(0)
                    net = Decimal(0)
                    tax = Decimal(0)

                    for key, value in row.items():
                        clean_key = key.strip()
                        if not value or value.strip() == '': continue
                        try:
                            clean_val = value.replace(',', '').replace('$', '').strip()
                            amount = Decimal(clean_val)
                            details[clean_key] = str(amount)
                            if clean_key == '5000': gross = amount
                            elif clean_key == '8000': net = amount
                            elif clean_key.startswith('6'): tax += abs(amount)
                        except InvalidOperation: continue

                    if row.get('Gross Pay'): gross = Decimal(row['Gross Pay'].replace(',', ''))
                    if row.get('Net Pay') or row.get('Net Salary'): 
                        val = row.get('Net Pay') or row.get('Net Salary')
                        net = Decimal(val.replace(',', ''))
                    if row.get('Total Tax'): tax = Decimal(row['Total Tax'].replace(',', ''))

                    results_to_create.append(PayrollResult(period=period, employee=emp, gross_pay=gross, net_pay=net, total_tax=tax, total_deductions=gross-net, details=details))
                    total_gross_sum += gross
                    total_net_sum += net
                    total_tax_sum += tax
                    row_count += 1

                PayrollResult.objects.bulk_create(results_to_create)
                period.total_gross = total_gross_sum
                period.total_net = total_net_sum
                period.total_tax = total_tax_sum
                period.total_amount = total_net_sum
                period.employee_count = row_count
                period.status = PeriodStatus.COMPLETED
                period.save()
                
                PayrollExecutionLog.objects.create(period=period, execution_type='historical_upload', status='completed', employee_count=row_count, executed_by=request.user)

            return render(request, 'payroll/historical_upload_result.html', {'success': True, 'count': row_count, 'period': period, 'company_id': company_id, 'country_slug': country_slug, 'payroll_id': payroll_id})

        except Exception as e:
            logger.error(f"Historical upload error: {e}")
            return render(request, 'payroll/historical_upload_result.html', {'success': False, 'error_message': str(e), 'period': period, 'company_id': company_id, 'country_slug': country_slug, 'payroll_id': payroll_id})

# ============================================================
# API UTILS
# ============================================================

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def get_next_period_number(request, payroll_id):
    return JsonResponse({'next_period_number': 1})

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
@require_POST
def lock_payroll(request, country_slug, company_id, payroll_id):
    return JsonResponse({'success': True})

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
@require_POST
def unlock_payroll(request, country_slug, company_id, payroll_id):
    return JsonResponse({'success': True})

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
@require_POST
def lock_period(request, country_slug, company_id, payroll_id, period_id):
    return JsonResponse({'success': True})

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
@require_POST
def unlock_period(request, country_slug, company_id, payroll_id, period_id):
    return JsonResponse({'success': True})

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def payroll_summary_api(request, payroll_id):
    return JsonResponse({'success': True})

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def payroll_base_audit(request, country_slug, company_id, payroll_id, period_id):
    return render(request, 'payroll/base_audit.html', {})