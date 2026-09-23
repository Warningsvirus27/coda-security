import logging
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from .activity_logger import ActivityLogger
from .models import UserActivityLog

logger = logging.getLogger(__name__)


class UserActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivityLog
        fields = ['id', 'username', 'action', 'description', 'details', 'ip_address', 'created_at']


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        username_or_email = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')

        if not username_or_email or not password:
            return Response(
                {'error': 'Username/email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Allow logging in with either username or email
        user = authenticate(request, username=username_or_email, password=password)
        if user is None and '@' in username_or_email:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            if not user.is_active:
                return Response({'error': 'Account is disabled.'}, status=status.HTTP_403_FORBIDDEN)

            login(request, user)
            ActivityLogger.log(
                request=request,
                action='USER_LOGIN',
                description=f'User {user.username} logged in successfully',
                user=user,
            )
            return Response({
                'authenticated': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
            })

        ActivityLogger.log(
            request=request,
            action='LOGIN_FAILED',
            description=f'Failed login attempt for {username_or_email}',
            details={'attempted_username': username_or_email},
        )
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get('username', '').strip()
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()

        if not username or not password or not email:
            return Response(
                {'error': 'Username, email, and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username__iexact=username).exists():
            return Response({'error': 'A user with this username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email__iexact=email).exists():
            return Response({'error': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        ActivityLogger.log(
            request=request,
            action='USER_REGISTER',
            description=f'New user registered: {user.username}',
            user=user,
        )

        return Response({
            'authenticated': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = request.user
        username = user.username if user.is_authenticated else 'anonymous'
        ActivityLogger.log(
            request=request,
            action='USER_LOGOUT',
            description=f'User {username} logged out',
            user=user if user.is_authenticated else None,
        )
        logout(request)
        return Response({'status': 'logged_out', 'authenticated': False})


class CurrentUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                'authenticated': True,
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'is_staff': request.user.is_staff,
                },
            })
        return Response({'authenticated': False})


class GoogleSSOView(APIView):
    """
    Handles Google SSO sign-in/registration via ID token or authorization code.
    Creates or links local user and logs in session.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        name = request.data.get('name', '').strip()
        google_id = request.data.get('google_id', '')

        if not email:
            return Response({'error': 'Email is required for Google SSO.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create user corresponding to Google account
        user = User.objects.filter(email__iexact=email).first()
        created = False
        if not user:
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username__iexact=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            first_name = name.split(' ')[0] if name else ''
            last_name = ' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else ''

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            user.set_unusable_password()
            user.save()
            created = True

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        ActivityLogger.log(
            request=request,
            action='GOOGLE_SSO_LOGIN',
            description=f'User {user.username} logged in via Google SSO ({"new user" if created else "existing"})',
            details={'google_id': google_id, 'is_new_user': created},
            user=user,
        )

        return Response({
            'authenticated': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'created': created,
        })


class UserActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Class-based viewset to query user activities and change logs.
    Strictly filters activities to the currently logged in user.
    """
    serializer_class = UserActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['action']
    search_fields = ['action', 'description', 'ip_address']
    ordering_fields = ['created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # Strictly show activities for the currently logged-in user
            return UserActivityLog.objects.filter(
                Q(user=user) | Q(username=user.username)
            ).order_by('-created_at')
        return UserActivityLog.objects.none()
