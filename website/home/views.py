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



from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages

@require_POST
def demo_request(request):
    first_name = request.POST.get("first_name", "").strip()
    last_name  = request.POST.get("last_name", "").strip()
    user_email = request.POST.get("email", "").strip()  # email do utilizador
    company    = request.POST.get("company", "").strip()
    employees  = request.POST.get("employees", "").strip()
    region     = request.POST.get("region", "").strip()

    # Destinatário interno (TU)
    to_email = getattr(settings, "DEMO_REQUEST_TO_EMAIL", None) or "antoniorocha@exactuspay.com"

    subject = f"New demo request — {company or 'Unknown company'}"
    body = (
        f"New demo request\n\n"
        f"Name: {first_name} {last_name}\n"
        f"Work email: {user_email}\n"
        f"Company: {company}\n"
        f"Employees: {employees}\n"
        f"Region: {region or 'Not specified'}\n"
        f"IP: {request.META.get('REMOTE_ADDR')}\n"
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,     # "Exactus Support <no-reply@exactuspay.com>"
        to=[to_email],                              # <-- SEMPRE para ti
        reply_to=[user_email] if user_email else None,  # <-- responder ao utilizador
    )

    email.send(fail_silently=False)

    messages.success(request, "Thanks! We’ll contact you shortly.")
    return HttpResponseRedirect(reverse("home:demo"))



