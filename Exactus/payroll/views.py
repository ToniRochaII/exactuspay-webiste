import json
import csv
import io
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.views import View
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
from Exactus.utils.decorators import role_required

try:
    from Exactus.calculationbase.models import CalculationBase
except ImportError:
    CalculationBase = None

try:
    from Exactus.elements.models import Element
except ImportError:
    Element = None

# Ensure HistoricalUploadForm is imported from your forms.py
from .forms import (
    PayrollForm, 
    PayrollPeriodForm, 
    PayrollProcessForm, 
    HistoricalUploadForm
)

try:
    from Exactus.payroll.calculator.universal import UniversalPayrollCalculator
except ImportError:
    UniversalPayrollCalculator = None

logger = logging.getLogger(__name__)

# ============================================================
# PAYROLL DASHBOARD
# ============================================================

@login_required
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
# PAYROLL CREATE
# ============================================================

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


# ============================================================
# PAYROLL UPDATE
# ============================================================

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


# ============================================================
# PAYROLL DELETE
# ============================================================

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
            },
        )


# ============================================================
# PERIOD LIST
# ============================================================

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
# PERIOD DETAIL (GROSS TO NET REPORT)
# ============================================================

class PayrollPeriodDetailView(LoginRequiredMixin, DetailView):
    model = PayrollPeriod
    template_name = "payroll/period_detail.html"
    context_object_name = "period"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = self.object
        eligible_employees = period.get_eligible_employees()
        company_id = self.kwargs["company_id"]
        
        # 1. BUILD HEADER MAP (Code -> Readable Name)
        header_map = {}
        
        # A. Elements (Visible)
        if Element:
            visible_elems = Element.objects.filter(
                country=period.payroll.country,
                element_status__iexact='Visible'
            )
            for el in visible_elems:
                header_map[el.element_code] = el.element_name

        # B. PD Codes (Visible)
        pd_codes = PDcode.objects.filter(company_id=company_id, pdcode_status='Visible')
        for pd in pd_codes:
            header_map[pd.pdcode_code] = pd.pdcode_name

        # C. FORCE STANDARD HEADERS (FIXED: Added all standard codes)
        header_map.update({
            '5000': 'Gross Pay',
            '6000': 'Income Tax',
            '7000': 'National Insurance',       
            '8000': 'Net Salary',
            '9000': 'Employer Contributions'
        })

        # 2. GATHER DATA & FILTER COLUMNS
        report_rows = []
        active_codes = set() 
        
        # Only fetch stored results if we are NOT in Pending state.
        use_stored_results = period.status != PeriodStatus.PENDING
        
        payroll_results = period.results.select_related('employee').all()
        has_results = payroll_results.exists()
        
        if use_stored_results and has_results:
            loop_target = payroll_results
        else:
            loop_target = eligible_employees[:10000] # Preview limit

        for obj in loop_target:
            emp = obj.employee if hasattr(obj, 'employee') else obj
            row_data = {}
            
            if use_stored_results and hasattr(obj, 'details'):
                # History Mode (Locked/Processed Data)
                details = self._parse_details(obj.details)
                for k, v in details.items():
                    # Handle legacy key names just in case
                    if k == 'Gross Pay': k = '5000'
                    if k == 'Net Salary': k = '8000'
                    row_data[k] = self._safe_float(v)
            else:
                # Preview Mode (Live Calculation)
                if UniversalPayrollCalculator:
                    try:
                        calc = UniversalPayrollCalculator(period=period, employee=emp)
                        out = calc.calculate()
                        
                        # Extract Elements (Bases, Tax, Net)
                        for k, v in out.get('elements', {}).items():
                            row_data[k] = float(v)
                            
                        # Extract Earnings (PD Codes)
                        for pd_item in out.get('pd_codes', []):
                            code = pd_item['code']
                            if code not in row_data:
                                row_data[code] = float(pd_item['amount'])
                    except Exception as e:
                        logger.error(f"Preview error for {emp}: {e}")

            # FILTER: Show column if ANYONE has value > 0
            for k, v in row_data.items():
                # We check if it exists in our header_map OR is a standard key
                if k in header_map and abs(v) > 0:
                    active_codes.add(k)

            report_rows.append({'employee': emp, 'data': row_data})

        # 3. SORT HEADERS
        def strict_numerical_sort(val):
            try: return int(val)
            except: return 999999
            
        sorted_codes = sorted(list(active_codes), key=strict_numerical_sort)
        final_headers = []
        for code in sorted_codes:
            final_headers.append({
                'code': code,
                'label': header_map.get(code, code)
            })

        # 4. BUILD TABLE ROWS
        table_rows = []
        grand_totals = [Decimal('0.00')] * len(final_headers)

        for item in report_rows:
            cells = []
            for idx, h in enumerate(final_headers):
                val = item['data'].get(h['code'], 0.0)
                
                # Visual Logic:
                # Deductions (6000-7999) -> Show absolute (Positive in UI)
                try:
                    code_int = int(h['code'])
                    if 6000 <= code_int <= 7999: 
                        val = abs(val)
                except: pass
                
                cells.append(val)
                grand_totals[idx] += Decimal(str(val))
            
            table_rows.append({
                'employee_name': f"{item['employee'].employee_name} {item['employee'].employee_surname}",
                'employee_id': getattr(item['employee'], 'employee_id', item['employee'].id),
                'cells': cells
            })

        # 5. PERMISSION CHECKS FOR BUTTONS
        user = self.request.user
        allowed_approvers = ["EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION",
                             "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE"]
        
        # Safe permission check
        user_role = getattr(user, 'role', '').upper() if hasattr(user, 'role') else ''
        can_approve = False
        
        if user.is_superuser:
            can_approve = True
        elif hasattr(user, 'roles'): # Maybe ManyToMany
             can_approve = user.roles.filter(name__in=allowed_approvers).exists()
        elif user_role:
             can_approve = user_role in allowed_approvers

        context.update({
            'headers': final_headers,
            'rows': table_rows,
            'totals': grand_totals,
            'company_id': company_id,
            'country_slug': self.kwargs['country_slug'],
            'payroll_id': self.kwargs['payroll_id'],
            'process_form': PayrollProcessForm(),
            # Button Logic Flags
            'can_process': period.status == PeriodStatus.PENDING,
            'can_reset': period.status == PeriodStatus.PROCESSED,
            'can_send_approval': period.status == PeriodStatus.PROCESSED,
            'can_reject': period.status == PeriodStatus.AWAITING_APPROVAL and can_approve,
            'can_authorize': period.status == PeriodStatus.AWAITING_APPROVAL and can_approve,
            'is_locked': period.status == PeriodStatus.COMPLETED,
        })
        return context

    def _parse_details(self, details_data):
        if isinstance(details_data, str):
            try: return json.loads(details_data)
            except: return {}
        return details_data or {}

    def _safe_float(self, val):
        try: return float(val)
        except: return 0.0


# ============================================================
# PERIOD CREATE, UPDATE, DELETE
# ============================================================

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
        # Redirect to Historical Upload if Payroll is flagged as historical
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
        
        # Default behavior for regular payrolls
        return reverse_lazy("payroll:period_detail", kwargs={
            "country_slug": self.kwargs["country_slug"],
            "company_id": self.kwargs["company_id"],
            "payroll_id": self.kwargs["payroll_id"],
            "pk": self.object.pk,
        })


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
# PROCESS PERIOD (STAGE 1 -> STAGE 2)
# ============================================================

@method_decorator(login_required, name="dispatch")
class PayrollPeriodProcessView(View):
    def post(self, request, country_slug, company_id, payroll_id, period_id):
        period = get_object_or_404(PayrollPeriod, pk=period_id, payroll_id=payroll_id, payroll__company_id=company_id)
        
        # Start Log
        PayrollExecutionLog.objects.create(
            period=period, execution_type="calculation", status="started",
            input_data={"period_id": period_id}, executed_by=request.user
        )

        try:
            period.mark_as_processing(request.user)
            employees = period.get_eligible_employees()
            if not employees.exists(): raise ValueError("No eligible employees found.")

            with transaction.atomic():
                # 1. Clear old results
                PayrollResult.objects.filter(period=period).delete()
                
                results_to_create = []
                batch_total_gross = Decimal('0')
                batch_total_net = Decimal('0')
                batch_total_tax = Decimal('0')

                for emp in employees:
                    if UniversalPayrollCalculator:
                        try:
                            calc = UniversalPayrollCalculator(period=period, employee=emp)
                            output = calc.calculate()
                            totals = output.get('totals', {})
                            
                            final_gross = Decimal(str(totals.get('gross', 0)))
                            final_net = Decimal(str(totals.get('net', 0)))

                            # Skip zero-net employees for Additional Runs
                            if getattr(period, 'is_additional', False) and final_net == 0:
                                continue 
                            
                            final_deductions = final_gross - final_net
                            
                            elements_dict = output.get('elements', {})
                            json_storage = {k: str(v) for k, v in elements_dict.items()}
                            
                            results_to_create.append(PayrollResult(
                                period=period, 
                                employee=emp,
                                gross_pay=final_gross, 
                                net_pay=final_net, 
                                total_tax=final_deductions,
                                total_deductions=final_deductions,
                                details=json_storage
                            ))
                            batch_total_gross += final_gross
                            batch_total_net += final_net
                            batch_total_tax += final_deductions
                        except Exception as e:
                            logger.error(f"Calculator failed for {emp}: {e}")

                    else:
                        raise ImportError("UniversalPayrollCalculator not found")

                PayrollResult.objects.bulk_create(results_to_create)
                
                # MARK AS PROCESSED (Stage 2)
                period.mark_as_processed(results_payload={
                    "total_net": str(batch_total_net), 
                    "total_gross": str(batch_total_gross),
                    "total_tax": str(batch_total_tax)
                })

            return JsonResponse({"success": True, "message": f"Processed {len(results_to_create)} employees. Review required."})

        except Exception as e:
            period.status = PeriodStatus.PENDING
            period.save()
            return JsonResponse({"success": False, "error": str(e)}, status=500)


# ============================================================
# NEW WORKFLOW ACTIONS (MANUAL PERMISSION CHECKS)
# ============================================================

@method_decorator(login_required, name="dispatch")
class PayrollPeriodSendApprovalView(View):
    """
    Stage 2 -> Stage 3: Lock and Send to Approver
    """
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
class PayrollPeriodAuthorizeView(View):
    """
    Stage 3 -> Stage 4: Authorize and Finalize
    """
    def post(self, request, country_slug, company_id, payroll_id, period_id):
        try:
            # 1. Manual Role Check
            allowed_roles = ["EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION",
                             "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE"]
            
            user = request.user
            has_permission = False
            
            if user.is_superuser:
                has_permission = True
            elif hasattr(user, 'roles'): # Check ManyToMany
                has_permission = user.roles.filter(name__in=allowed_roles).exists()
            elif hasattr(user, 'role'): # Check simple field
                role_str = str(user.role).upper()
                has_permission = role_str in allowed_roles
            
            if not has_permission:
                 return JsonResponse({"success": False, "error": "Permission Denied: You are not authorized to approve payroll."}, status=403)

            # 2. Logic
            period = get_object_or_404(PayrollPeriod, pk=period_id, payroll_id=payroll_id)
            
            if period.status != PeriodStatus.AWAITING_APPROVAL:
                 return JsonResponse({"success": False, "error": "Period is not awaiting approval."}, status=400)
                 
            period.authorize(request.user)
            
            # Log execution
            PayrollExecutionLog.objects.create(
                period=period, execution_type="approval", status="completed",
                input_data={"action": "authorize"}, executed_by=request.user
            )
            
            messages.success(request, f"Period {period.name} authorized and completed.")
            return JsonResponse({"success": True})

        except Exception as e:
            # Catch all errors (DB, Logic) and return JSON
            return JsonResponse({"success": False, "error": f"Authorization Failed: {str(e)}"}, status=500)


@method_decorator(login_required, name="dispatch")
class PayrollPeriodRejectView(View):
    """
    Stage 3 -> Stage 1: Reject and Reset to Pending (Wipe Data)
    """
    def post(self, request, country_slug, company_id, payroll_id, period_id):
        try:
            # 1. Manual Role Check
            allowed_roles = ["EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION",
                             "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE"]
            
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

            # 2. Logic
            period = get_object_or_404(PayrollPeriod, pk=period_id, payroll_id=payroll_id)
            
            if period.status != PeriodStatus.AWAITING_APPROVAL:
                 return JsonResponse({"success": False, "error": "Period is not awaiting approval."}, status=400)
            
            with transaction.atomic():
                # Clear Results
                PayrollResult.objects.filter(period=period).delete()
                
                # Unmark Compensation Components
                CompensationComponent.objects.filter(
                    processed=True,
                    processed_period=period.name
                ).update(
                    processed=False,
                    processed_period=''
                )

                # Reject (Set status to PENDING)
                period.reject()
                
                # Log execution
                PayrollExecutionLog.objects.create(
                    period=period, execution_type="approval", status="cancelled",
                    input_data={"action": "reject"}, executed_by=request.user
                )

            messages.warning(request, f"Period {period.name} rejected. Data wiped and reset to open stage.")
            return JsonResponse({"success": True})
            
        except Exception as e:
            # Catch all errors and return JSON
            return JsonResponse({"success": False, "error": f"Rejection Failed: {str(e)}"}, status=500)


# ============================================================
# EXPORT & RESET UTILS
# ============================================================
@method_decorator(login_required, name='dispatch')
@method_decorator(role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION",
                                "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE"), 
                                name='dispatch')
class PayrollPeriodExportView(View):
    def get(self, request, country_slug, company_id, payroll_id, period_id):
        period = get_object_or_404(PayrollPeriod, pk=period_id)
        results = PayrollResult.objects.filter(period=period).select_related('employee')
        
        # 1. BUILD HEADER MAP (FIXED: Added all standard codes)
        header_map = {}
        
        if Element:
            visible_elems = Element.objects.filter(
                country=period.payroll.country,
                element_status__iexact='Visible'
            )
            for el in visible_elems:
                header_map[el.element_code] = el.element_name

        pd_codes = PDcode.objects.filter(company_id=company_id, pdcode_status='Visible')
        for pd in pd_codes:
            header_map[pd.pdcode_code] = pd.pdcode_name

        header_map.update({
            '5000': 'Gross Pay',
            '6000': 'Total Tax',
            '7000': 'Total NI',       
            '8000': 'Net Salary',
            '9000': 'Employer Contributions'
        })

        # 2. GATHER DATA & IDENTIFY ACTIVE COLUMNS
        rows_data = []
        active_codes = set()

        for res in results:
            details = res.details
            if isinstance(details, str):
                try: details = json.loads(details)
                except: details = {}
            elif not isinstance(details, dict):
                details = {}

            for k, v in details.items():
                try:
                    val = float(v)
                    # Check against header map to allow dynamic codes + standard ones
                    if abs(val) > 0 and (k in header_map or k in ['5000', '8000']):
                        active_codes.add(k)
                except: pass
            
            rows_data.append({
                'employee': res.employee,
                'details': details
            })

        # 3. SORT HEADERS
        def strict_numerical_sort(val):
            try: return int(val)
            except: return 999999
            
        sorted_codes = sorted(list(active_codes), key=strict_numerical_sort)

        # 4. GENERATE CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="Report_{period.name}.csv"'
        writer = csv.writer(response)
        
        # File Header
        writer.writerow([f"Gross to Net Report: {period.name}"])
        writer.writerow([]) 

        # Table Headers Row 1: Human Readable Names
        csv_headers = ['Employee ID', 'Employee Name'] + [header_map.get(c, c) for c in sorted_codes]
        writer.writerow(csv_headers)

        # Table Headers Row 2: Raw Codes (pdcodes)
        csv_codes = ['', ''] + [str(c) for c in sorted_codes]
        writer.writerow(csv_codes)
        
        # Initialize Totals Map
        col_totals = {code: Decimal('0.00') for code in sorted_codes}

        # Data Rows
        for item in rows_data:
            emp = item['employee']
            details = item['details']
            
            row = [
                getattr(emp, 'employee_id', ''),
                f"{emp.employee_name} {emp.employee_surname}"
            ]
            
            for code in sorted_codes:
                val = details.get(code, 0.0)
                try:
                    val = float(val)
                    # Visual Logic: Show Deductions (6000-7999) as positive
                    if 6000 <= int(code) <= 7999:
                        val = abs(val)
                except: 
                    val = 0.0
                
                # Add to total (using Decimal for precision)
                col_totals[code] += Decimal(str(val))

                row.append(f"{val:.2f}")
                
            writer.writerow(row)

        # Totals Row
        totals_row = ['', 'TOTALS']
        for code in sorted_codes:
            totals_row.append(f"{col_totals[code]:.2f}")
            
        writer.writerow(totals_row)
            
        return response


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION",
               "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE")
@require_http_methods(["GET", "POST"])
def payroll_reset_confirm(request, country_slug, company_id, payroll_id):
    payroll = get_object_or_404(Payroll, pk=payroll_id, company_id=company_id)

    if request.method == "POST":
        try:
            with transaction.atomic():
                PayrollPeriod.objects.filter(payroll=payroll).update(
                    status=PeriodStatus.PENDING, total_gross=0, total_net=0, total_tax=0, total_amount=0
                )
                PayrollResult.objects.filter(period__payroll=payroll).delete()
                
                messages.success(request, f"Successfully reset Payroll FY{payroll.fiscal_year}.")
                return redirect('payroll:payroll_detail', country_slug=country_slug, company_id=company_id, pk=payroll.pk)
        except Exception as e:
            messages.error(request, f"Error: {e}")

    context = {'payroll': payroll, 'company_id': company_id, 'country_slug': country_slug}
    return render(request, 'payroll/payroll_reset_confirm.html', context)


@login_required
@require_POST
def reset_payroll(request, country_slug, company_id, payroll_id):
    payroll = get_object_or_404(Payroll, pk=payroll_id, company_id=company_id)
    try:
        with transaction.atomic():
            PayrollPeriod.objects.filter(payroll=payroll).update(
                status=PeriodStatus.PENDING, total_gross=0, total_net=0, total_tax=0
            )
            PayrollResult.objects.filter(period__payroll=payroll).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION",
               "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE")
@require_http_methods(["GET", "POST"])
def payroll_period_reset_confirm(request, country_slug, company_id, payroll_id, period_id):
    """
    Handles manual reset (Stage 2 -> Stage 1) via separate page or POST
    """
    period = get_object_or_404(PayrollPeriod, pk=period_id, payroll_id=payroll_id)

    if request.method == "POST":
        try:
            with transaction.atomic():
                # 1. Clear Results
                PayrollResult.objects.filter(period=period).delete()
                
                # 2. Unmark Compensation Components
                CompensationComponent.objects.filter(
                    processed=True,
                    processed_period=period.name
                ).update(
                    processed=False,
                    processed_period=''
                )

                # 3. Reset Period to PENDING
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


@login_required
def payroll_base_audit(request, country_slug, company_id, payroll_id, period_id):
    period = get_object_or_404(PayrollPeriod, pk=period_id)
    employees = period.get_eligible_employees()
    audit_data = []
    # Only useful if BasePayrollCalculator exists
    try:
        from Exactus.payroll.calculator.base import BasePayrollCalculator
        for emp in employees:
            calc = BasePayrollCalculator(emp, period)
            audit_data.append({
                'employee': emp,
                'totals': {'taxable_gross': calc.taxable_gross}
            })
    except ImportError:
        pass
        
    context = {
        'period': period,
        'audit_data': audit_data,
        'country_slug': country_slug, 
        'company_id': company_id,
        'payroll_id': payroll_id
    }
    return render(request, 'payroll/base_audit.html', context)


@login_required
def get_next_period_number(request, payroll_id):
    return JsonResponse({'next_period_number': 1})

@login_required
@require_POST
def lock_payroll(request, country_slug, company_id, payroll_id):
    return JsonResponse({'success': True})

@login_required
@require_POST
def unlock_payroll(request, country_slug, company_id, payroll_id):
    return JsonResponse({'success': True})

@login_required
@require_POST
def lock_period(request, country_slug, company_id, payroll_id, period_id):
    return JsonResponse({'success': True})

@login_required
@require_POST
def unlock_period(request, country_slug, company_id, payroll_id, period_id):
    return JsonResponse({'success': True})

@login_required
def payroll_summary_api(request, payroll_id):
    return JsonResponse({'success': True})

# ============================================================
# HISTORICAL DATA UPLOAD
# ============================================================

class PayrollHistoricalUploadView(LoginRequiredMixin, View):
    """
    Upload historical data via CSV. Validates columns against Elements/PD Codes.
    """
    def get(self, request, country_slug, company_id, payroll_id, period_id):
        # Ensure we only upload to historical payrolls
        period = get_object_or_404(PayrollPeriod, pk=period_id, payroll__is_historical=True)
        form = HistoricalUploadForm()
        context = {
            'form': form,
            'period': period,
            'company_id': company_id,
            'country_slug': country_slug,
            'payroll_id': payroll_id
        }
        return render(request, 'payroll/historical_upload.html', context)

    def post(self, request, country_slug, company_id, payroll_id, period_id):
        period = get_object_or_404(PayrollPeriod, pk=period_id, payroll__is_historical=True)
        form = HistoricalUploadForm(request.POST, request.FILES)
        
        context = {
            'form': form, 'period': period, 'company_id': company_id, 
            'country_slug': country_slug, 'payroll_id': payroll_id
        }

        if not form.is_valid():
            return render(request, 'payroll/historical_upload.html', context)

        file = request.FILES['file']
        
        try:
            decoded_file = file.read().decode('utf-8-sig') # Handle BOM if present
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            headers = reader.fieldnames or []
        except Exception as e:
            messages.error(request, f"Error reading CSV: {e}")
            return render(request, 'payroll/historical_upload.html', context)
        
        # 1. VALIDATION: Check Headers against Database
        # ---------------------------------------------
        company = get_object_or_404(Company, pk=company_id)
        country = get_object_or_404(Country, slug=country_slug)
        
        # Fetch all valid codes from DB
        db_elements = set(Element.objects.filter(country=country).values_list('element_code', flat=True))
        db_pdcodes = set(PDcode.objects.filter(company=company).values_list('pdcode_code', flat=True))
        
        # Standard columns that don't need code validation
        ignored_cols = [
            'Employee ID', 'Employee Code', 'Employee Name', 'Name', 'Surname', 
            'Gross Pay', 'Net Salary', 'Total Tax', 'Total Deductions', 'Net Pay'
        ]
        
        missing_codes = []
        
        for header in headers:
            # Clean header (strip spaces)
            clean_header = header.strip()
            
            # Skip standard columns
            if clean_header in ignored_cols:
                continue
            
            # Check if it exists in DB
            if clean_header not in db_elements and clean_header not in db_pdcodes:
                missing_codes.append(clean_header)

        # IF MISSING CODES FOUND -> STOP AND REPORT
        if missing_codes:
            return render(request, 'payroll/historical_upload_result.html', {
                'success': False,
                'missing_codes': missing_codes,
                'period': period,
                'company_id': company_id, 
                'country_slug': country_slug, 
                'payroll_id': payroll_id
            })

        # 2. PROCESSING: Import Data
        # ---------------------------------------------
        try:
            with transaction.atomic():
                # --- FIX: TRANSITION THROUGH 'PROCESSING' STATE ---
                period.status = PeriodStatus.PROCESSING
                period.processed_by = request.user
                period.processed_at = timezone.now()
                period.save()
                
                # Clear existing data for this period (it's a re-upload)
                PayrollResult.objects.filter(period=period).delete()
                
                results_to_create = []
                row_count = 0
                
                # Totals for Period update
                total_gross_sum = Decimal(0)
                total_net_sum = Decimal(0)
                total_tax_sum = Decimal(0)

                # Reset file pointer
                io_string.seek(0)
                reader = csv.DictReader(io_string)

                for row in reader:
                    # Identify Employee
                    emp_id = row.get('Employee ID') or row.get('Employee Code')
                    if not emp_id: continue
                    
                    emp = Employee.objects.filter(company_id=company_id, employee_id=emp_id).first()
                    # Fallback to employee_code if needed
                    if not emp:
                        emp = Employee.objects.filter(company_id=company_id, employee_code=emp_id).first()
                    
                    if not emp:
                        # You might want to collect missing employees to report as well
                        continue

                    details = {}
                    gross = Decimal(0)
                    net = Decimal(0)
                    tax = Decimal(0)

                    # Parse columns
                    for key, value in row.items():
                        clean_key = key.strip()
                        if not value or value.strip() == '': continue
                        
                        try:
                            clean_val = value.replace(',', '').replace('$', '').strip()
                            amount = Decimal(clean_val)
                            
                            # Store in details JSON
                            details[clean_key] = str(amount)
                            
                            # Heuristic for totals if specific columns aren't provided
                            # (Usually Gross/Net are mapped to specific codes like 5000/8000 in your system)
                            if clean_key == '5000': gross = amount
                            elif clean_key == '8000': net = amount
                            elif clean_key.startswith('6'): tax += abs(amount) # Assumption: 6xxx are taxes
                            
                        except InvalidOperation:
                            continue # Skip non-numeric data

                    # Prefer explicit columns if they exist in CSV
                    if row.get('Gross Pay'): 
                        gross = Decimal(row['Gross Pay'].replace(',', ''))
                    if row.get('Net Pay') or row.get('Net Salary'): 
                        val = row.get('Net Pay') or row.get('Net Salary')
                        net = Decimal(val.replace(',', ''))
                    if row.get('Total Tax'):
                        tax = Decimal(row['Total Tax'].replace(',', ''))

                    results_to_create.append(PayrollResult(
                        period=period,
                        employee=emp,
                        gross_pay=gross,
                        net_pay=net,
                        total_tax=tax,
                        total_deductions=gross-net,
                        details=details
                    ))
                    
                    total_gross_sum += gross
                    total_net_sum += net
                    total_tax_sum += tax
                    row_count += 1

                # Bulk Create Results
                PayrollResult.objects.bulk_create(results_to_create)
                
                # Update Period
                period.total_gross = total_gross_sum
                period.total_net = total_net_sum
                period.total_tax = total_tax_sum
                period.total_amount = total_net_sum
                period.employee_count = row_count
                period.status = PeriodStatus.COMPLETED
                period.save()
                
                # Log execution
                PayrollExecutionLog.objects.create(
                    period=period,
                    execution_type='historical_upload',
                    status='completed',
                    employee_count=row_count,
                    executed_by=request.user
                )

            return render(request, 'payroll/historical_upload_result.html', {
                'success': True,
                'count': row_count,
                'period': period,
                'company_id': company_id, 
                'country_slug': country_slug, 
                'payroll_id': payroll_id
            })

        except Exception as e:
            logger.error(f"Historical upload error: {e}")
            return render(request, 'payroll/historical_upload_result.html', {
                'success': False,
                'error_message': str(e),
                'period': period,
                'company_id': company_id, 
                'country_slug': country_slug, 
                'payroll_id': payroll_id
            })