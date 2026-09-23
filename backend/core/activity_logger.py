from typing import Any, Dict, Optional
from django.contrib.auth.models import AnonymousUser
from .models import UserActivityLog


class ActivityLogger:
    """Helper class to record user activities and changes."""

    @staticmethod
    def get_client_ip(request) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    @classmethod
    def log(
        cls,
        request,
        action: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        user=None,
    ) -> UserActivityLog:
        if user is None and request and hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            user = request.user

        username = user.username if user and not isinstance(user, AnonymousUser) else 'anonymous'
        ip_address = cls.get_client_ip(request) if request else ''
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''

        return UserActivityLog.objects.create(
            user=user if (user and not isinstance(user, AnonymousUser)) else None,
            username=username,
            action=action,
            description=description,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
