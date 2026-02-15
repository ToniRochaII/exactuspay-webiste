from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request,'home/index.html')

def platform(request):
    return render(request,'platform.html')

def features(request):
    return render(request,'features.html')

def security(request):
    return render(request,'security.html')

def pricing(request):
    return render(request,'pricing.html')

def resources(request):
    return render(request,'resources.html')



# home/views.py
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

def demo_page(request):
    # renders your demo.html template
    return render(request, "demo.html", {"current_year": 2026})

@require_POST
def demo_request(request):
    first_name = (request.POST.get("first_name") or "").strip()
    last_name  = (request.POST.get("last_name") or "").strip()
    email      = (request.POST.get("email") or "").strip()
    company    = (request.POST.get("company") or "").strip()
    employees  = (request.POST.get("employees") or "").strip()
    region     = (request.POST.get("region") or "").strip()

    # Minimal validation (HTML required helps, but never trust the browser)
    missing = [k for k, v in {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "company": company,
        "employees": employees,
    }.items() if not v]

    if missing:
        messages.error(request, "Please complete all required fields.")
        return redirect("home:demo")

    subject = f"New Demo Request — {company}"
    body = (
        "A new demo request was submitted:\n\n"
        f"Name: {first_name} {last_name}\n"
        f"Work Email: {email}\n"
        f"Company: {company}\n"
        f"Employees: {employees}\n"
        f"Region: {region or 'Not sure yet'}\n\n"
        f"Source path: {request.get_full_path()}\n"
        f"IP: {request.META.get('REMOTE_ADDR', '')}\n"
    )

    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[getattr(settings, "DEMO_REQUEST_TO_EMAIL", "antoniorocha@exactuspay.com")],
        reply_to=[email],  # So you can hit “Reply” and answer the requester
    )

    try:
        msg.send(fail_silently=False)
        messages.success(request, "Thanks! Your request was received. We'll contact you shortly.")
    except Exception:
        messages.error(request, "We couldn't send your request right now. Please try again shortly.")

    return redirect("home:demo")
