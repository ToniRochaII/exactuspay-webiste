# employee/utils/progress.py
import json
from django.http import JsonResponse
from django.utils.module_loading import import_string
from django.conf import settings

def get_upload_progress(request):
    """
    Get upload progress from session
    """
    progress_id = request.GET.get('progress_id')
    if progress_id:
        progress_data = request.session.get(f'upload_progress_{progress_id}', {})
        return JsonResponse(progress_data)
    return JsonResponse({'error': 'No progress ID provided'})

class UploadProgressMixin:
    """
    Mixin to handle upload progress tracking
    """
    def get_progress_id(self, request):
        """Generate a unique progress ID for this upload"""
        return request.POST.get('progress_id') or str(hash(request.META['REMOTE_ADDR'] + str(request.META.get('REMOTE_PORT', ''))))
    
    def update_progress(self, request, current, total, status="processing"):
        """Update progress in session"""
        progress_id = self.get_progress_id(request)
        progress_data = {
            'current': current,
            'total': total,
            'percent': int((current / total) * 100) if total > 0 else 0,
            'status': status
        }
        request.session[f'upload_progress_{progress_id}'] = progress_data
        request.session.modified = True