# Exactus/payroll/views.py - FIXED IMPORTS
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse_lazy
from django.views import View
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from django.utils.decorators import method_decorator  # ADD THIS IMPORT

from Exactus.company.models import Company
from Exactus.country.models import Country
from .models import (
    Payroll, PayrollPeriod, PayrollExecutionLog, 
    PayrollStatus, PeriodStatus
)
from .forms import PayrollForm, PayrollPeriodForm, PayrollAdjustmentForm, PayrollProcessForm


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
        
        # Add annotations for summary data
        return queryset.annotate(
            period_count=Count('periods'),
            total_amount=Sum('periods__total_amount')
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
        
        # Get periods with their totals
        periods = payroll.periods.all().order_by("period_number")
        
        # Calculate summary
        summary = {
            'total_periods': periods.count(),
            'pending_periods': periods.filter(status=PeriodStatus.PENDING).count(),
            'completed_periods': periods.filter(status=PeriodStatus.COMPLETED).count(),
            'locked_periods': periods.filter(status=PeriodStatus.LOCKED).count(),
            'total_amount': periods.aggregate(total=Sum('total_amount'))['total'] or 0,
            'total_employees': periods.aggregate(total=Sum('employee_count'))['total'] or 0,
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

    def form_valid(self, form):
        company = get_object_or_404(Company, pk=self.kwargs["company_id"])
        country = get_object_or_404(Country, slug=self.kwargs["country_slug"])

        payroll = form.instance
        payroll.company = company
        payroll.country = country
        payroll.created_by = self.request.user
        payroll.status = PayrollStatus.DRAFT

        try:
            payroll.full_clean()  # Run model validation
            response = super().form_valid(form)
            messages.success(self.request, f"Payroll created for {company.trade_name} - FY{payroll.fiscal_year}")
            return response
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

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

    def dispatch(self, request, *args, **kwargs):
        payroll = self.get_object()
        if not payroll.is_editable:
            messages.error(request, f"Cannot edit payroll with status: {payroll.get_status_display()}")
            return redirect(
                "payroll:payroll_detail",
                country_slug=self.kwargs["country_slug"],
                company_id=self.kwargs["company_id"],
                pk=payroll.pk,
            )
        return super().dispatch(request, *args, **kwargs)

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

    def dispatch(self, request, *args, **kwargs):
        payroll = self.get_object()
        if not payroll.is_deletable:
            messages.error(request, f"Cannot delete payroll with status: {payroll.get_status_display()}")
            return redirect(
                "payroll:payroll_detail",
                country_slug=self.kwargs["country_slug"],
                company_id=self.kwargs["company_id"],
                pk=payroll.pk,
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_id"] = self.kwargs["company_id"]
        context["country_slug"] = self.kwargs["country_slug"]
        return context

    def delete(self, request, *args, **kwargs):
        payroll = self.get_object()
        payroll.status = PayrollStatus.CANCELLED
        payroll.save()
        messages.success(request, f"Payroll FY{payroll.fiscal_year} has been cancelled.")
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
# PERIOD DETAIL
# ============================================================

class PayrollPeriodDetailView(LoginRequiredMixin, DetailView):
    model = PayrollPeriod
    template_name = "payroll/period_detail.html"
    context_object_name = "period"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = self.get_object()
        
        # Get recent execution logs
        execution_logs = period.execution_logs.all().order_by('-started_at')[:10]
        adjustments = period.adjustments.all().order_by('-created_at')
        
        context["execution_logs"] = execution_logs
        context["adjustments"] = adjustments
        context["company_id"] = self.kwargs["company_id"]
        context["country_slug"] = self.kwargs["country_slug"]
        context["payroll_id"] = self.kwargs["payroll_id"]
        
        # Add process form for AJAX processing
        context["process_form"] = PayrollProcessForm()

        return context


# ============================================================
# PERIOD CREATE
# ============================================================

class PayrollPeriodCreateView(LoginRequiredMixin, CreateView):
    model = PayrollPeriod
    form_class = PayrollPeriodForm
    template_name = "payroll/period_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.payroll = get_object_or_404(Payroll, pk=self.kwargs["payroll_id"])
        if not self.payroll.can_add_periods:
            messages.error(request, f"Cannot add periods to payroll with status: {self.payroll.get_status_display()}")
            return redirect(
                "payroll:payroll_detail",
                country_slug=self.kwargs["country_slug"],
                company_id=self.kwargs["company_id"],
                pk=self.payroll.pk,
            )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['payroll'] = self.payroll
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial['payroll'] = self.payroll
        
        # Auto-suggest dates
        today = timezone.now().date()
        last_period = PayrollPeriod.objects.filter(payroll=self.payroll).order_by('end_date').last()
        
        if last_period:
            # Start from day after last period ends
            initial['start_date'] = last_period.end_date + timezone.timedelta(days=1)
            initial['end_date'] = last_period.end_date + timezone.timedelta(days=30)
        else:
            # First period of the fiscal year
            initial['start_date'] = today.replace(day=1)
            initial['end_date'] = (today.replace(day=1) + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)
        
        # Processing date: end date + 5 days
        if initial.get('end_date'):
            initial['processing_date'] = initial['end_date'] + timezone.timedelta(days=5)
            initial['payment_date'] = initial['end_date'] + timezone.timedelta(days=7)
        
        return initial

    def form_valid(self, form):
        form.instance.payroll = self.payroll
        form.instance.created_by = self.request.user
        
        # Auto-generate name if not provided
        if not form.instance.name and form.instance.start_date:
            form.instance.name = form.instance.start_date.strftime('%B %Y')
        
        try:
            response = super().form_valid(form)
            messages.success(self.request, f"Period {form.instance.period_number} created successfully.")
            
            # Log the creation
            PayrollExecutionLog.objects.create(
                period=form.instance,
                execution_type='creation',
                status='completed',
                input_data={'period_data': form.cleaned_data},
                output_data={'period_id': form.instance.pk},
                executed_by=self.request.user
            )
            
            return response
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
        return reverse_lazy(
            "payroll:period_detail",
            kwargs={
                "country_slug": self.kwargs["country_slug"],
                "company_id": self.kwargs["company_id"],
                "payroll_id": self.kwargs["payroll_id"],
                "pk": self.object.pk,
            },
        )


# ============================================================
# PERIOD UPDATE
# ============================================================

class PayrollPeriodUpdateView(LoginRequiredMixin, UpdateView):
    model = PayrollPeriod
    form_class = PayrollPeriodForm
    template_name = "payroll/period_form.html"

    def dispatch(self, request, *args, **kwargs):
        period = self.get_object()
        if not period.is_editable:
            messages.error(request, f"Cannot edit period with status: {period.get_status_display()}")
            return redirect(
                "payroll:period_detail",
                country_slug=self.kwargs["country_slug"],
                company_id=self.kwargs["company_id"],
                payroll_id=self.kwargs["payroll_id"],
                pk=period.pk,
            )
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

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, f"Period {form.instance.period_number} updated successfully.")
            
            # Log the update
            PayrollExecutionLog.objects.create(
                period=form.instance,
                execution_type='update',
                status='completed',
                input_data={'period_data': form.cleaned_data},
                output_data={'period_id': form.instance.pk},
                executed_by=self.request.user
            )
            
            return response
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy(
            "payroll:period_detail",
            kwargs={
                "country_slug": self.kwargs["country_slug"],
                "company_id": self.kwargs["company_id"],
                "payroll_id": self.kwargs["payroll_id"],
                "pk": self.object.pk,
            },
        )


# ============================================================
# PERIOD DELETE
# ============================================================

class PayrollPeriodDeleteView(LoginRequiredMixin, DeleteView):
    model = PayrollPeriod
    template_name = "payroll/period_confirm_delete.html"

    def dispatch(self, request, *args, **kwargs):
        period = self.get_object()
        if not period.is_deletable:
            messages.error(request, f"Cannot delete period with status: {period.get_status_display()}")
            return redirect(
                "payroll:period_detail",
                country_slug=self.kwargs["country_slug"],
                company_id=self.kwargs["company_id"],
                payroll_id=self.kwargs["payroll_id"],
                pk=period.pk,
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_id"] = self.kwargs["company_id"]
        context["country_slug"] = self.kwargs["country_slug"]
        context["payroll_id"] = self.kwargs["payroll_id"]
        return context

    def delete(self, request, *args, **kwargs):
        period = self.get_object()
        period_number = period.period_number
        period_name = period.name
        
        # Log before deletion
        PayrollExecutionLog.objects.create(
            period=period,
            execution_type='deletion',
            status='completed',
            input_data={'period_id': period.pk, 'period_name': period_name},
            output_data={'deleted': True},
            executed_by=request.user
        )
        
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Period '{period_name}' (#{period_number}) deleted successfully.")
        return response

    def get_success_url(self):
        return reverse_lazy(
            "payroll:period_list",
            kwargs={
                "country_slug": self.kwargs["country_slug"],
                "company_id": self.kwargs["company_id"],
                "payroll_id": self.kwargs["payroll_id"],
            },
        )


# ============================================================
# PROCESS PERIOD (AJAX)
# ============================================================

# FIX: Use method_decorator for class-based view
@method_decorator(login_required, name='dispatch')
class PayrollPeriodProcessView(View):
    def post(self, request, country_slug, company_id, payroll_id, period_id):
        period = get_object_or_404(
            PayrollPeriod,
            id=period_id,
            payroll_id=payroll_id,
            payroll__company_id=company_id
        )
        
        if not period.can_process:
            return JsonResponse({
                "success": False,
                "error": f"Cannot process period with status: {period.get_status_display()}"
            }, status=400)
        
        # Start processing
        try:
            # Create execution log
            execution_log = PayrollExecutionLog.objects.create(
                period=period,
                execution_type='calculation',
                status='started',
                input_data={'period_id': period_id},
                executed_by=request.user
            )
            
            # Mark period as processing
            if period.mark_as_processing(request.user):
                # Simulate processing (replace with actual payroll calculation)
                # TODO: Integrate with actual payroll calculation engine
                
                # Simulate delay for processing
                import time
                time.sleep(2)  # Remove this in production
                
                # Mock results
                mock_results = {
                    'employee_count': 42,
                    'total_gross': 125000.00,
                    'total_deductions': 25000.00,
                    'total_net': 100000.00,
                    'total_tax': 15000.00,
                    'total_amount': 100000.00,
                    'success': True
                }
                
                # Mark as completed
                if period.mark_as_completed(mock_results):
                    execution_log.mark_completed({
                        'results': mock_results,
                        'processing_time': 2.5,
                        'success': True
                    })
                    
                    return JsonResponse({
                        "success": True,
                        "message": "Payroll processing completed successfully",
                        "results": mock_results,
                        "redirect_url": reverse_lazy(
                            "payroll:period_detail",
                            kwargs={
                                "country_slug": country_slug,
                                "company_id": company_id,
                                "payroll_id": payroll_id,
                                "pk": period_id,
                            },
                        )
                    })
                else:
                    execution_log.mark_failed("Failed to mark period as completed")
                    return JsonResponse({
                        "success": False,
                        "error": "Failed to complete processing"
                    }, status=500)
            else:
                return JsonResponse({
                    "success": False,
                    "error": "Could not start processing"
                }, status=400)
                
        except Exception as e:
            # Log the error
            if 'execution_log' in locals():
                execution_log.mark_failed(str(e))
            
            return JsonResponse({
                "success": False,
                "error": f"Processing error: {str(e)}"
            }, status=500)


# ============================================================
# AJAX VIEWS FOR TEMPLATE FUNCTIONALITY
# ============================================================

@login_required
def get_next_period_number(request, payroll_id):
    """Get the next period number for a payroll (AJAX)"""
    payroll = get_object_or_404(Payroll, pk=payroll_id)
    last_period = PayrollPeriod.objects.filter(payroll=payroll).order_by('period_number').last()
    
    next_number = last_period.period_number + 1 if last_period else 1
    
    return JsonResponse({
        'next_period_number': next_number,
        'payroll_id': payroll_id,
        'fiscal_year': payroll.fiscal_year
    })


@login_required
def lock_payroll(request, country_slug, company_id, payroll_id):
    """Lock a payroll (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    payroll = get_object_or_404(
        Payroll,
        pk=payroll_id,
        company_id=company_id
    )
    
    try:
        payroll.lock(request.user)
        return JsonResponse({
            'success': True,
            'message': f'Payroll FY{payroll.fiscal_year} locked successfully',
            'status': payroll.status,
            'locked_at': payroll.locked_at.isoformat() if payroll.locked_at else None
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def unlock_payroll(request, country_slug, company_id, payroll_id):
    """Unlock a payroll (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    payroll = get_object_or_404(
        Payroll,
        pk=payroll_id,
        company_id=company_id
    )
    
    try:
        payroll.unlock()
        return JsonResponse({
            'success': True,
            'message': f'Payroll FY{payroll.fiscal_year} unlocked successfully',
            'status': payroll.status,
            'locked_at': None
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def lock_period(request, country_slug, company_id, payroll_id, period_id):
    """Lock a payroll period (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    period = get_object_or_404(
        PayrollPeriod,
        pk=period_id,
        payroll_id=payroll_id
    )
    
    try:
        period.lock()
        return JsonResponse({
            'success': True,
            'message': f'Period {period.name} locked successfully',
            'status': period.status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def unlock_period(request, country_slug, company_id, payroll_id, period_id):
    """Unlock a payroll period (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    period = get_object_or_404(
        PayrollPeriod,
        pk=period_id,
        payroll_id=payroll_id
    )
    
    try:
        period.unlock()
        return JsonResponse({
            'success': True,
            'message': f'Period {period.name} unlocked successfully',
            'status': period.status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ============================================================
# DASHBOARD AND SUMMARY VIEWS
# ============================================================

@login_required
def payroll_dashboard(request, country_slug, company_id):
    """Payroll dashboard view"""
    company = get_object_or_404(Company, pk=company_id)
    country = get_object_or_404(Country, slug=country_slug)
    
    # Get active payrolls
    active_payrolls = Payroll.objects.filter(
        company=company,
        status__in=[PayrollStatus.DRAFT, PayrollStatus.RUNNING]
    ).order_by('-fiscal_year')
    
    # Get recent periods
    recent_periods = PayrollPeriod.objects.filter(
        payroll__company=company
    ).order_by('-created_at')[:10]
    
    # Calculate statistics
    total_payrolls = Payroll.objects.filter(company=company).count()
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


@login_required
def payroll_summary_api(request, payroll_id):
    """API endpoint for payroll summary (AJAX)"""
    payroll = get_object_or_404(Payroll, pk=payroll_id)
    
    summary = payroll.get_periods_summary()
    
    return JsonResponse({
        'success': True,
        'summary': summary,
        'payroll': {
            'id': payroll.pk,
            'fiscal_year': payroll.fiscal_year,
            'status': payroll.status,
            'status_display': payroll.get_status_display(),
            'is_editable': payroll.is_editable,
            'is_deletable': payroll.is_deletable,
        }
    })