from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from social_django.utils import load_strategy, load_backend
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class GoogleExchangeView(APIView):
    """
    Exchanges a Google OAuth2 access token for platform JWT tokens.
    Creates the user account automatically on first sign-in and marks
    the email as verified. No password is required for Google-authenticated users.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=["Authentication / Authorization"],
        operation_summary="Exchange a Google OAuth access token for JWT tokens",
        operation_description=(
            "Accepts a Google OAuth2 `access_token` obtained from the client-side Google sign-in flow "
            "and exchanges it for a platform JWT `access` + `refresh` token pair.\n\n"
            "If the Google account has not been seen before, a new user is created automatically "
            "with `email_verified=True`.\n\n"
            "**Flow:**\n"
            "1. Frontend initiates Google sign-in and receives a Google `access_token`\n"
            "2. Frontend calls this endpoint with that token\n"
            "3. Platform validates the token with Google, finds or creates the user, and returns JWTs\n"
            "4. Frontend stores the JWTs and uses the `access` token as a Bearer header"
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["access_token"],
            properties={
                "access_token": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Google OAuth2 access token from the client-side sign-in",
                ),
            },
            example={"access_token": "ya29.a0AfH6SMBT..."},
        ),
        responses={
            200: openapi.Response(
                description="JWT tokens issued",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="JWT refresh token (long-lived)"),
                        "access":  openapi.Schema(type=openapi.TYPE_STRING, description="JWT access token (short-lived)"),
                    },
                    example={
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "access":  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    },
                ),
            ),
            400: openapi.Response(description="Missing or malformed access_token"),
            403: openapi.Response(description="Google OAuth validation failed or user account is inactive"),
        },
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

        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified"])

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_200_OK)
