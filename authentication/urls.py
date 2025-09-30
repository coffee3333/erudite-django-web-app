from django.urls import path

from authentication.views.login_view import LoginView, LogoutView
from authentication.views.register_view import RegisterView

urlpatterns = [
    # Authentication
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    path('auth/registration/', RegisterView.as_view(), name='registration'),
]
