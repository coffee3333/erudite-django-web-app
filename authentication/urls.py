from django.urls import path, include, re_path

from authentication.views.google_oauth import GoogleExchangeView
from authentication.views.login_view import LoginView, LogoutView
from authentication.views.register_view import RegisterView
from authentication.views.reset_password_view import RequestPasswordOTPView, ConfirmPasswordOTPView
from authentication.views.verify_email_view import RequestEmailVerificationView, ConfirmEmailVerificationView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Authentication
    path('auth/registration/', RegisterView.as_view(), name='registration'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # Password reset по OTP
    path('auth/password/reset/request/', RequestPasswordOTPView.as_view(), name='password-reset-request'),
    path('auth/password/reset/confirm/', ConfirmPasswordOTPView.as_view(), name='password-reset-confirm'),

    # Email verification
    path('users/me/email/verify/request/', RequestEmailVerificationView.as_view(), name='email-verify-request'),
    path('users/me/email/verify/confirm/', ConfirmEmailVerificationView.as_view(), name='email-verify-confirm'),

    path("oauth/", include("social_django.urls", namespace="social")),
    # обмен access-token Google → наши JWT
    path("auth/google/", GoogleExchangeView.as_view()),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
