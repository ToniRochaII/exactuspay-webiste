# Exactus/accounts/services/onboarding.py

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class OnboardingService:
    @staticmethod
    def onboard_employee(username, email, role="EMPLOYEE", password=None, created_by_user=None):
        """
        Creates a new user account.
        If 'password' is provided (e.g., Tax ID), it uses that.
        Otherwise, it generates a random password.
        """
        
        # 1. Determine Password
        if password:
            final_password = password
            password_msg = "Your initial password is your Tax ID / National ID."
        else:
            final_password = User.objects.make_random_password()
            password_msg = f"Your temporary password is: {final_password}"

        # 2. Create User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=final_password
        )
        
        # 3. Set Attributes
        user.role = role
        user.is_active = True
        user.save()

        # 4. Send Welcome Email
        site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        
        subject = f"Welcome to ExactusPay - Account Created"
        message = (
            f"Hello,\n\n"
            f"An account has been created for you at ExactusPay.\n\n"
            f"Username: {username}\n"
            f"{password_msg}\n\n"
            f"Please log in at: {site_url}/login/\n\n"
            f"Best regards,\nExactusPay Team"
        )
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
        except Exception as e:
            # Log error but don't fail the transaction
            print(f"Failed to send onboarding email: {e}")

        return user