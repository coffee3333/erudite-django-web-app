from django.urls import path, include, re_path

from authentication.views.google_oauth import GoogleExchangeView
from authentication.views.login_view import LoginView, LogoutView
from authentication.views.register_view import RegisterView
from authentication.views.profile_view import MeProfileView, MeProfileUpdateView
from authentication.views.reset_password_view import RequestPasswordOTPView, ConfirmPasswordOTPView
from authentication.views.verify_email_view import RequestEmailVerificationView, ConfirmEmailVerificationView
from authentication.views.leaderboard_view import LeaderboardView
from authentication.views.dashboard_view import DashboardView
from authentication.views.teacher_dashboard_view import TeacherDashboardView
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
    path("auth/google/", GoogleExchangeView.as_view(), name='google-exchange'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('profile/me/', MeProfileView.as_view(), name='profile'),
    path('profile/me/update/', MeProfileUpdateView.as_view(), name='profile-update'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('teacher-dashboard/', TeacherDashboardView.as_view(), name='teacher-dashboard'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
