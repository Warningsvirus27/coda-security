from django.urls import path
from .views import ScanViewSet

scan_view = ScanViewSet.as_view({
    'get': 'status',
})

urlpatterns = [
    path('', scan_view, name='scan-status-default'),
    path('trigger/', ScanViewSet.as_view({'post': 'trigger'}), name='scan-trigger'),
    path('history/', ScanViewSet.as_view({'get': 'history'}), name='scan-history'),
    path('status/', ScanViewSet.as_view({'get': 'status'}), name='scan-status'),
]
