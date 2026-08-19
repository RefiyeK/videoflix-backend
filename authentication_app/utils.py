from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

User = get_user_model()


def build_activation_link(user):
    """Build the frontend activation URL with an encoded uid and token."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return (
        f"{settings.FRONTEND_URL}/pages/auth/activate.html"
        f"?uid={uidb64}&token={token}"
    )


def send_activation_email(user_id):
    """Send the account activation email. Runs inside an RQ worker."""
    user = User.objects.get(pk=user_id)
    activation_link = build_activation_link(user)
    subject = "Confirm your email"
    message = (
        "Thank you for registering with Videoflix.\n\n"
        "Please activate your account by clicking the link below:\n"
        f"{activation_link}\n\n"
        "If you did not create an account, please ignore this email."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def get_user_from_uidb64(uidb64):
    """Decode a base64-encoded uid and return the matching user, or None."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def set_jwt_cookies(response, access_token, refresh_token):
    """Attach access and refresh JWT tokens as HttpOnly cookies to a response."""
    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        value=str(access_token),
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
    )
    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
        value=str(refresh_token),
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
    )


def set_access_cookie(response, access_token):
    """Set only the access token cookie (used when refreshing)."""
    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        value=str(access_token),
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
    )
