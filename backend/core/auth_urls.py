from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .auth_views import (
    LoginView,
    RegisterView,
    LogoutView,
    CurrentUserView,
    GoogleSSOView,
    UserActivityLogViewSet,
)

router = DefaultRouter()
router.register(r'activities', UserActivityLogViewSet, basename='user-activity')

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', CurrentUserView.as_view(), name='auth-me'),
    path('status/', CurrentUserView.as_view(), name='auth-status'),
    path('google/', GoogleSSOView.as_view(), name='auth-google'),
    path('', include(router.urls)),
]
