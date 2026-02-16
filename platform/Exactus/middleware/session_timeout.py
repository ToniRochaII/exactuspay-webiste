"""
Session timeout middleware for 5-minute idle logout.
Backend safety net that works with cached_db sessions.
"""
import time
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class SessionTimeoutMiddleware(MiddlewareMixin):
    """Enforces 5-minute idle timeout at the server level."""
    
    # 5 minutes in seconds
    TIMEOUT_SECONDS = 300
    
    def process_request(self, request):
        # Only check authenticated users
        if not request.user.is_authenticated:
            return None
        
        current_time = time.time()
        last_activity = request.session.get('last_activity')
        
        # Check if session has expired
        if last_activity:
            idle_time = current_time - last_activity
            
            if idle_time > self.TIMEOUT_SECONDS:
                # Session expired - logout user
                logout(request)
                request.session['session_expired'] = True
                
                # Show message
                messages.warning(
                    request,
                    'Your session has expired due to inactivity. '
                    'Please log in again.'
                )
                
                # Handle AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'session_expired',
                        'redirect': reverse('login'),
                        'message': 'Session expired'
                    }, status=403)
                
                # Redirect regular requests
                return redirect(f"{reverse('login')}?session_expired=true")
        
        # Update last activity timestamp
        request.session['last_activity'] = current_time
        return None
    
    def process_response(self, request, response):
        """Clean session data on logout."""
        if not request.user.is_authenticated:
            request.session.pop('last_activity', None)
        return response