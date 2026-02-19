from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext as _
import logging

logger = logging.getLogger(__name__)

def home_view(request):
    return render(request, 'index.html')

def features_view(request):
    return render(request, 'features.html')

def platform_view(request):
    return render(request, 'platform.html')

def security_view(request):
    return render(request, 'security.html')

def pricing_view(request):
    return render(request, 'pricing.html')

def demo_view(request):
    return render(request, 'demo.html')

def demo_request_view(request):
    """Handles the form submission from demo.html and sends the email."""
    if request.method == 'POST':
        # 1. Extract data from the form
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        company = request.POST.get('company', '').strip()
        employees = request.POST.get('employees', '').strip()
        region = request.POST.get('region', 'Not sure yet').strip()

        # 2. Basic Validation
        if not all([first_name, last_name, email, company, employees]):
            messages.error(request, _("Please fill out all required fields."))
            return redirect('home:demo')

        # 3. Construct the Email
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

        # 4. Send the Email
        try:
            send_mail(
                subject=subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEMO_REQUEST_TO_EMAIL],
                fail_silently=False,
            )
            # 5. Show success message on the frontend
            messages.success(request, _("Thank you! Your demo request has been sent successfully. We will contact you soon."))

        except Exception as e:
            logger.error(f"Failed to send demo request email: {e}")
            messages.error(request, _("There was a technical error sending your request. Please try again later."))

        # Redirect back to the demo page so the user sees the alert message
        return redirect('home:demo')

    # If someone tries to visit the URL directly without submitting the form
    return redirect('home:demo')