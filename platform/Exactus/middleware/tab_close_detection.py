"""
Handles browser tab close detection via Beacon API.
"""
import time
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


class TabCloseMiddleware(MiddlewareMixin):
    """Detects when users close browser tabs."""
    
    def process_request(self, request):
        # Handle Beacon API tab close notifications
        if (request.method == 'POST' and 
            request.path == '/ajax/tab-close/' and
            request.POST.get('tab_closed') == 'true'):
            
            if request.user.is_authenticated:
                # Log the event (optional - could write to database)
                username = request.user.username
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                print(f"[TabClose] {username} closed tab at {timestamp}")
            
            # Beacon expects empty 204 response
            return HttpResponse(status=204)
        
        return None