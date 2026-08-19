import django_rq
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.tokens import default_token_generator
from authentication_app.utils import send_activation_email, get_user_from_uidb64, set_jwt_cookies, set_access_cookie
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import RegistrationSerializer


class RegisterView(APIView):
    """Register a new (inactive) user and queue the activation email."""

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        queue = django_rq.get_queue("default")
        queue.enqueue(send_activation_email, user.id)

        token = default_token_generator.make_token(user)
        return Response(
            {
                "user": {"id": user.id, "email": user.email},
                "token": token,
            },
            status=status.HTTP_201_CREATED,
        )


class ActivateView(APIView):
    """Activate a user account using the emailed uid and token."""

    def get(self, request, uidb64, token):
        user = get_user_from_uidb64(uidb64)
        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response(
                {"message": "Account successfully activated."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "Activation failed."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(APIView):
    """Authenticate a user and set JWT tokens as HttpOnly cookies."""

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                'detail': 'Login successful',
                'user': {'id': user.id, 'username': user.email},
            },
            status=status.HTTP_200_OK,
        )
        set_jwt_cookies(response, refresh.access_token, refresh)
        return response


class LogoutView(APIView):
    """Blacklist the refresh token and delete the auth cookies."""

    def post(self, request):
        refresh_token = request.COOKIES.get(
            settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token missing.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass  # token already invalid or expired

        response = Response(
            {'detail': 'Logout successful! All tokens will be deleted. '
                       'Refresh token is now invalid.'},
            status=status.HTTP_200_OK,
        )
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        return response


class CookieTokenRefreshView(APIView):
    """Issue a new access token from the refresh cookie."""

    def post(self, request):
        refresh_token = request.COOKIES.get(
            settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token missing.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            refresh = RefreshToken(refresh_token)
            access = refresh.access_token
        except TokenError:
            return Response(
                {'detail': 'Invalid refresh token.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = Response(
            {'detail': 'Token refreshed', 'access': str(access)},
            status=status.HTTP_200_OK,
        )
        set_access_cookie(response, access)
        return response
