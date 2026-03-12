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
    
# Exactus/accounts/middleware.py
from django.conf import settings
from django.utils import translation

class UserPreferredLanguageMiddleware:
    """
    If a logged-in user has a preferred_language set in their Profile,
    force that language for the request and persist it in the session.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            profile = getattr(user, "userprofile", None)
            lang = getattr(profile, "preferred_language", None)

            if lang and lang in dict(settings.LANGUAGES):
                translation.activate(lang)
                request.LANGUAGE_CODE = lang
                request.session["django_language"] = lang

        response = self.get_response(request)

        translation.deactivate()
        return response
