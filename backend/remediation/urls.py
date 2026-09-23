from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RemediationViewSet, AuditLogViewSet

router = DefaultRouter()
router.register(r'audit-log', AuditLogViewSet, basename='remediation-audit-log')
router.register(r'', RemediationViewSet, basename='remediation')

urlpatterns = [
    path('', include(router.urls)),
]
