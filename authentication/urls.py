from django.urls import path, include

from authentication.views.login_view import LoginView, LogoutView
from authentication.views.register_view import RegisterView
from authentication.views.google_oauth import GoogleExchangeView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Authentication
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    path('auth/registration/', RegisterView.as_view(), name='registration'),

    # Google O-Auth
    path("oauth/", include("social_django.urls", namespace="social")),
    path("auth/google/", GoogleExchangeView.as_view()),

    # Token Refresh
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
