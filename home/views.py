import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


def index(request):
    return render(request, "home/index.html")


def platform(request):
    return render(request, "home/platform.html")


def features(request):
    return render(request, "home/features.html")


def security(request):
    return render(request, "home/security.html")


def pricing(request):
    return render(request, "home/pricing.html")


def resources(request):
    return render(request, "home/resources.html")


def demo_page(request):
    return render(request, "home/demo.html", {"current_year": 2026})


@require_POST
def demo_request(request):
    first_name = (request.POST.get("first_name") or "").strip()
    last_name = (request.POST.get("last_name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    company = (request.POST.get("company") or "").strip()
    employees = (request.POST.get("employees") or "").strip()
    region = (request.POST.get("region") or "").strip()

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
        reply_to=[email] if email else None,
    )

    try:
        msg.send(fail_silently=False)
        messages.success(request, "Thanks! Your request was received. We'll contact you shortly.")
    except Exception:
        logger.exception("Demo request email failed to send")
        messages.error(request, "We couldn't send your request right now. Please try again shortly.")

    return redirect("home:demo")
