from django.urls import path
from .views import ConfigViewSet

urlpatterns = [
    path('', ConfigViewSet.as_view({'get': 'list', 'put': 'update', 'patch': 'update'}), name='config-detail'),
    path('validate-token/', ConfigViewSet.as_view({'post': 'validate_token'}), name='config-validate-token'),
    path('slack-status/', ConfigViewSet.as_view({'get': 'slack_status'}), name='config-slack-status'),
]
