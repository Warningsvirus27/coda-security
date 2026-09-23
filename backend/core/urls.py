"""
SecureCoda — Core URL Configuration (Documents & Audit Log)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, AuditLogViewSet

router = DefaultRouter()
router.register(r'', DocumentViewSet, basename='document')

# Audit log is under /api/documents/audit-log/ for organizational clarity,
# but could also be mounted separately.
audit_router = DefaultRouter()
audit_router.register(r'audit-log', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(audit_router.urls)),
]
