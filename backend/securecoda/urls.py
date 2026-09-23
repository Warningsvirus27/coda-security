"""
SecureCoda — Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def api_root(request):
    """API root endpoint with version info."""
    return JsonResponse({
        'name': 'SecureCoda API',
        'version': '1.0.0',
        'description': 'Security monitoring and remediation for Coda',
        'endpoints': {
            'alerts': '/api/alerts/',
            'documents': '/api/documents/',
            'remediation': '/api/remediation/',
            'scan': '/api/scan/',
            'config': '/api/config/',
            'auth': '/api/auth/',
            'reports': '/api/reports/',
        }
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root'),
    path('api/alerts/', include('alerts.urls')),
    path('api/documents/', include('core.urls')),
    path('api/remediation/', include('remediation.urls')),
    path('api/scan/', include('scanner.urls')),
    path('api/config/', include('config.urls')),
    path('api/reports/', include('core.report_urls')),

    # Auth endpoints (Google SSO via allauth)
    path('accounts/', include('allauth.urls')),

    # Session auth status for React frontend
    path('api/auth/', include('core.auth_urls')),
]
