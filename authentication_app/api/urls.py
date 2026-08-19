from django.urls import path

from .views import (
    RegisterView,
    ActivateView,
    LoginView,
    LogoutView,
    CookieTokenRefreshView,
    PasswordResetView,
    PasswordConfirmView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "activate/<uidb64>/<token>/",
        ActivateView.as_view(),
        name="activate",
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "token/refresh/",
        CookieTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "password_reset/",
        PasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password_confirm/<uidb64>/<token>/",
        PasswordConfirmView.as_view(),
        name="password_confirm",
    ),
]
