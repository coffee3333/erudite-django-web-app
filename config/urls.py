from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions


schema_view = get_schema_view(
   openapi.Info(
      title="Erudite API",
      default_version='v1',
      description="Documentation of Erudite API",
      contact=openapi.Contact(email="erudite@dhbw.com"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)
urlpatterns = [

    path('api/admin/', admin.site.urls),
    path('api/users/', include('authentication.urls')),
    path('api/platform/', include('core.urls')),

    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
