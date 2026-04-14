from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
import logging

from .article_library import BRAZIL_ARTICLES
from .forms import DemoRequestForm

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

    form = DemoRequestForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Please fill out all required fields."))
        return redirect("home:demo")

    demo_request = form.save()
    subject = f"New Demo Request: {demo_request.company} ({demo_request.first_name} {demo_request.last_name})"
    email_body = f"""
You have received a new demo request from the ExactusPay website.

Details:
-------------------------
Name: {demo_request.first_name} {demo_request.last_name}
Work Email: {demo_request.email}
Company: {demo_request.company}
Number of Employees: {demo_request.employees}
Expansion Region: {demo_request.region}
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

def brazil_article_detail_view(request, article_id):
    article = BRAZIL_ARTICLES.get(article_id)
    if not article:
        raise Http404("Article not found.")

    return render(request, article["template_name"])


def chile_article_0001(request):
    return render(request, "articles/cl/article_0001.html")


def costa_rica_article_0001(request):
    return render(request, "articles/cr/article_0001.html")
