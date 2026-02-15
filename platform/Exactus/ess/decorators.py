# decorators.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from functools import wraps

def employee_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        from django.apps import apps
        Employee = apps.get_model('employee', 'Employee')
        
        if not request.user.email:
            from django.contrib import messages
            messages.error(request, "User email not configured.")
            return redirect('home')
        
        try:
            employee = Employee.objects.get(email=request.user.email)
        except Employee.DoesNotExist:
            from django.contrib import messages
            messages.error(request, "Employee record not found.")
            return redirect('home')
            
        request.employee = employee
        return view_func(request, *args, **kwargs)
    return _wrapped_view