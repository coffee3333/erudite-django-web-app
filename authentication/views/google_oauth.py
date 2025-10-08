from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from social_django.utils import load_strategy, load_backend
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class GoogleExchangeView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Exchange Google OAuth access token for JWT tokens.",
        tags=['Authentication / Authorization'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['access_token'],
            properties={
                'access_token': openapi.Schema(type=openapi.TYPE_STRING, description='Google OAuth2 access token')
            }
        ),
        responses={
            200: openapi.Response(
                description="JWT tokens returned",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Bad Request: Missing access_token",
            403: "OAuth failed or user is inactive"
        }
    )
    def post(self, request):
        token = request.data.get("access_token")
        if not token:
            return Response({"detail": "missing access_token"}, status=status.HTTP_400_BAD_REQUEST)

        strategy = load_strategy(request)
        backend = load_backend(strategy, "google-oauth2", redirect_uri=None)

        user = backend.do_auth(token)
        if not user or not user.is_active:
            return Response({"detail": "OAuth failed"}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_200_OK)
