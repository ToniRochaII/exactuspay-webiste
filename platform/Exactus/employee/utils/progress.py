# employee/utils/progress.py
import json
from django.http import JsonResponse

def get_upload_progress(request):
    """
    Simple upload progress tracker
    """
    progress_id = request.GET.get('progress_id')
    if progress_id:
        # Simulate progress - in a real implementation, you'd track actual progress
        # For now, we'll simulate based on time or use session storage
        progress_data = request.session.get(f'upload_progress_{progress_id}', {
            'current': 0,
            'total': 100,
            'percent': 0,
            'status': 'Starting upload...'
        })
        return JsonResponse(progress_data)
    return JsonResponse({'error': 'No progress ID provided'})

def start_progress_tracking(request, progress_id, total_steps=100):
    """Initialize progress tracking"""
    request.session[f'upload_progress_{progress_id}'] = {
        'current': 0,
        'total': total_steps,
        'percent': 0,
        'status': 'Starting...'
    }
    request.session.modified = True

def update_progress(request, progress_id, current, total, status):
    """Update progress in session"""
    percent = int((current / total) * 100) if total > 0 else 0
    request.session[f'upload_progress_{progress_id}'] = {
        'current': current,
        'total': total,
        'percent': percent,
        'status': status
    }
    request.session.modified = True

def complete_progress(request, progress_id):
    """Mark progress as complete"""
    if f'upload_progress_{progress_id}' in request.session:
        del request.session[f'upload_progress_{progress_id}']