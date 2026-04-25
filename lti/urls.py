from django.urls import path
from .views import JWKSView, OIDCInitView, LTILaunchView, LTIConfigView

urlpatterns = [
    path("jwks/",       JWKSView.as_view(),      name="lti-jwks"),
    path("oidc-init/",  OIDCInitView.as_view(),  name="lti-oidc-init"),
    path("launch/",     LTILaunchView.as_view(),  name="lti-launch"),
    path("config/",     LTIConfigView.as_view(),  name="lti-config"),
]
