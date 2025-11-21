from django.shortcuts import render, get_object_or_404, redirect
from employee.models import Employee
from payregister.models import PayRegister
from payregister.forms import PayRegisterForm

def list_entries(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    entries = employee.payregister_entries.all()
    return render(request, 'payregister/list.html', {
        'employee': employee,
        'entries': entries,
    })

def create_entry(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == 'POST':
        form = PayRegisterForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.employee = employee
            obj.created_by = request.user
            obj.save()
            return redirect('payregister_list', employee_id=employee.id)
    else:
        form = PayRegisterForm()

    return render(request, 'payregister/create.html', {
        'employee': employee,
        'form': form
    })
