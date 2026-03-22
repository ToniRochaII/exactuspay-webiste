from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext as _
import logging

logger = logging.getLogger(__name__)

def home_view(request):
    return render(request, 'home/index.html')

def features_view(request):
    return render(request, 'home/features.html')

def platform_view(request):
    return render(request, 'home/platform.html')

def security_view(request):
    return render(request, 'home/security.html')

def pricing_view(request):
    return render(request, 'home/pricing.html')

def demo_view(request):
    return render(request, 'home/demo.html')

def demo_request_view(request):
    if request.method != "POST":
        return redirect("home:demo")

    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    email = request.POST.get("email", "").strip()
    company = request.POST.get("company", "").strip()
    employees = request.POST.get("employees", "").strip()
    region = request.POST.get("region", "Not sure yet").strip()

    if not all([first_name, last_name, email, company, employees]):
        messages.error(request, _("Please fill out all required fields."))
        return redirect("home:demo")

    subject = f"New Demo Request: {company} ({first_name} {last_name})"
    email_body = f"""
You have received a new demo request from the ExactusPay website.

Details:
-------------------------
Name: {first_name} {last_name}
Work Email: {email}
Company: {company}
Number of Employees: {employees}
Expansion Region: {region}
"""

    try:
        send_mail(
            subject=subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEMO_REQUEST_TO_EMAIL],
            fail_silently=False,
        )
        messages.success(
            request,
            _("Thank you! Your demo request has been sent successfully. We will contact you soon.")
        )
    except Exception:
        logger.exception("Failed to send demo request email")
        messages.error(
            request,
            _("There was a technical error sending your request. Please try again later.")
        )

    return redirect("home:demo")

def brazil_article_0001(request):
    return render(request, 'articles/br/article_0001.html')

def chile_article_0001(request):
    return render(request, 'articles/cl/article_0001.html')