from django.shortcuts import render
from django.conf import settings

class SiteLockMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Always allow admin, static files, media, login etc.
        if (
            request.path.startswith('/admin/')
            or request.path.startswith(settings.STATIC_URL)
            or request.path.startswith(settings.MEDIA_URL)
            or request.path.startswith('/accounts/')
        ):
            return self.get_response(request)

        # Control via settings (easy to toggle off later)
        if not getattr(settings, 'SITE_TEMPORARILY_CLOSED', True):
            return self.get_response(request)

        # Show thank-you + temporarily closed page
        context = {
            'thank_you_message': (
                "Thank you for your amazing support and patronage so far! "
                "Every order, like, share, and repost has meant the world to us."
            ),
            'explanation': (
                "We're taking the site down temporarily to prepare something much bigger. "
                "New heat, better experience, and some surprises are coming very soon."
            ),
            'when_back': "We'll be back stronger — stay locked in.",
            'social_links': True,  # optional flag to show IG/TikTok etc.
        }

        return render(request, 'store/thanks.html', context)