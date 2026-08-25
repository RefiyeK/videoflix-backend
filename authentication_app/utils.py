import django_rq
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


def build_activation_message(activation_link):
    """Compose the plain text body of the account activation email."""
    return (
        "Thank you for registering with Videoflix.\n\n"
        "Please activate your account by clicking the link below:\n"
        f"{activation_link}\n\n"
        "If you did not create an account, please ignore this email."
    )


def send_activation_email(user_id):
    """Send the account activation email. Runs inside an RQ worker."""
    user = User.objects.get(pk=user_id)
    message = build_activation_message(build_activation_link(user))
    send_mail(
        "Confirm your email",
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
    """Attach the access and refresh JWT cookies to the given response."""
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


def build_password_reset_link(user):
    """Build the frontend password reset URL with an encoded uid and token."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return (
        f"{settings.FRONTEND_URL}/pages/auth/confirm_password.html"
        f"?uid={uidb64}&token={token}"
    )


def build_password_reset_message(reset_link):
    """Compose the plain text body of the password reset email."""
    return (
        "We recently received a request to reset your password.\n\n"
        "If you made this request, click the link below to set a new one:\n"
        f"{reset_link}\n\n"
        "For security reasons this link is only valid for 24 hours.\n\n"
        "If you did not request a password reset, please ignore this email."
    )


def send_password_reset_email(user_id):
    """Send the password reset email. Runs inside an RQ worker."""
    user = User.objects.get(pk=user_id)
    message = build_password_reset_message(build_password_reset_link(user))
    send_mail(
        "Reset your Password",
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def queue_password_reset_email(email):
    """Queue the reset email only when an active user matches the email."""
    user = User.objects.filter(email=email, is_active=True).first()
    if user is not None:
        django_rq.get_queue("default").enqueue(
            send_password_reset_email, user.id)


def get_user_for_reset(uidb64, token):
    """Return the user if both the uid and the reset token are valid."""
    user = get_user_from_uidb64(uidb64)
    if user is not None and default_token_generator.check_token(user, token):
        return user
    return None


def set_new_password(user, new_password):
    """Persist the new password for the given user."""
    user.set_password(new_password)
    user.save()
