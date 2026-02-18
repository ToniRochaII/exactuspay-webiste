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



import logging
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

@require_POST
def demo_request(request):
    first_name = request.POST.get("first_name", "").strip()
    last_name  = request.POST.get("last_name", "").strip()
    user_email = request.POST.get("email", "").strip()
    company    = request.POST.get("company", "").strip()
    employees  = request.POST.get("employees", "").strip()
    region     = request.POST.get("region", "").strip()

    # valida email do utilizador (para o Reply-To)
    try:
        if user_email:
            validate_email(user_email)
    except ValidationError:
        messages.error(request, "Please enter a valid email address.")
        return HttpResponseRedirect(reverse("home:demo"))

    to_email = getattr(settings, "DEMO_REQUEST_TO_EMAIL", "") or "antoniorocha@exactuspay.com"

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

    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
            reply_to=[user_email] if user_email else [],
        )
        email.send(fail_silently=False)
        messages.success(request, "Thanks! We’ll contact you shortly.")
    except Exception as e:
        logger.exception("Demo request email failed: %s", e)
        messages.error(request, "We couldn't send your request right now. Please try again later.")

    return HttpResponseRedirect(reverse("home:demo"))


