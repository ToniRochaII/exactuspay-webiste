import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.db import transaction

# Safely import UserProfile if it exists
try:
    from Exactus.accounts.models import UserProfile
except ImportError:
    UserProfile = None

User = get_user_model()
logger = logging.getLogger(__name__)

class OnboardingService:
    """
    Service to handle the secure creation and onboarding of new users.
    """

    @staticmethod
    @transaction.atomic
    def onboard_employee(username, email, role='EMPLOYEE', created_by_user=None):
        """
        Creates a user, assigns a role, and sends a setup email.
        """
        if User.objects.filter(email=email).exists():
            raise ValueError(f"User with email {email} already exists.")

        if User.objects.filter(username=username).exists():
            raise ValueError(f"User with username {username} already exists.")

        # 1. Create the User (Unusable password initially)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=None  # User sets this via link
        )
        
        # 2. Assign Role (Handle both Custom User Model or UserProfile)
        if hasattr(user, 'role'):
            user.role = role
            user.save()
        
        # 3. Create/Update UserProfile (if your system uses it)
        if UserProfile:
            profile, created = UserProfile.objects.get_or_create(user=user)
            if hasattr(profile, 'role'):
                profile.role = role
                profile.save()

        # 4. Generate Activation Link
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Ensure this URL name matches your urls.py (usually 'password_reset_confirm')
        try:
            setup_url = settings.SITE_URL + reverse('password_reset_confirm', args=[uid, token])
        except Exception:
            # Fallback if SITE_URL isn't set or URL name differs
            setup_url = f"/accounts/reset/{uid}/{token}/"

        # 5. Send Welcome Email
        subject = "Welcome to ExactusPay - Activate Your Account"
        context = {
            'user': user,
            'setup_url': setup_url,
            'creator': created_by_user
        }
        
        # Render email templates (Ensure these exist in templates/emails/)
        try:
            html_message = render_to_string('emails/account_welcome.html', context)
            plain_message = render_to_string('emails/account_welcome.txt', context)
        except Exception:
            # Fallback simple message if templates are missing
            html_message = None
            plain_message = f"Welcome! Please set your password here: {setup_url}"

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f"Onboarded user {email} successfully.")
        return user