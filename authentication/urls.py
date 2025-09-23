from django.urls import path

from authentication.views.login_view import LoginView, LogoutView

urlpatterns = [
    # Authentication
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
]
