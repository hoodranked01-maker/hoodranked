from datetime import datetime
import pytz
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings

class SiteLockMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip lock for admin and static/media (optional but recommended)
        if request.path.startswith('/admin/') or \
           request.path.startswith(settings.STATIC_URL) or \
           request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        # Define unlock time (today 20:00 WAT)
        lagos_tz = pytz.timezone('Africa/Lagos')
        now = datetime.now(lagos_tz)
        
        # You can make this dynamic or come from settings / model later
        unlock_time_today = now.replace(hour=20, minute=0, second=0, microsecond=0)

        if not getattr(settings, 'SITE_LOCK_ENABLED', False):
            return self.get_response(request)

        lagos_tz = pytz.timezone('Africa/Lagos')
        now = datetime.now(lagos_tz)
        unlock_time = now.replace(
            hour=getattr(settings, 'SITE_UNLOCK_HOUR', 20),
            minute=getattr(settings, 'SITE_UNLOCK_MINUTE', 0),
            second=0, microsecond=0
        )

        if now >= unlock_time:
            return self.get_response(request)

        # Otherwise → show teaser page
        # You can also check if it's before 8 PM on a specific date only
        # e.g. if now.date() == datetime(2025, 2, 21).date() and now < unlock_time_today:

        context = {
            'unlock_time': unlock_time_today.strftime('%I:%M %p WAT'),  # 8:00 PM WAT
            'current_time': now.strftime('%I:%M:%S %p'),
        }

        return render(request, 'store/teaser.html', context)