# Exactus/accounts/middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class ForcePasswordChangeMiddleware:
    """
    Middleware that forces users to change their password if the 
    'force_password_change' flag is set on their profile.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check if profile exists and requires reset
            if hasattr(request.user, 'userprofile') and request.user.userprofile.force_password_change:
                
                # List of URLs allowed while in "forced reset" mode
                allowed_paths = [
                    reverse('password_change'),      # The form
                    reverse('password_change_done'), # The success page (Critical to prevent loops)
                    reverse('logout'),               # Allow them to leave
                ]
                
                if request.path not in allowed_paths:
                    return redirect('password_change')

        return self.get_response(request)