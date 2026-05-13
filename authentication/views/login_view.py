from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.serializers import LoginSerializer, LogoutSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class LoginView(generics.GenericAPIView):
    """
    Authenticates a user with email + password and returns a JWT token pair.
    The access token is short-lived; use the refresh token to obtain a new one.
    """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=["Authentication / Authorization"],
        operation_summary="Log in and obtain JWT tokens",
        operation_description=(
            "Authenticate with email and password. Returns a **JWT access token** (short-lived) "
            "and a **refresh token** (long-lived).\n\n"
            "- Attach the access token as `Authorization: Bearer <access>` on every protected request.\n"
            "- When the access token expires, call `POST /api/users/token/refresh/` with the refresh token to obtain a new access token.\n"
            "- To end the session, call `POST /api/users/auth/logout/` to blacklist the refresh token."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email":    openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Registered email address"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, format="password", description="Account password"),
            },
            example={"email": "student@example.com", "password": "MyStr0ngPass!"},
        ),
        responses={
            200: openapi.Response(
                description="Login successful — returns JWT token pair",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access":  openapi.Schema(type=openapi.TYPE_STRING, description="Short-lived JWT access token"),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="Long-lived JWT refresh token"),
                    },
                    example={
                        "access":  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    },
                ),
            ),
            400: openapi.Response(description="Missing or invalid fields"),
            401: openapi.Response(description="Wrong email or password"),
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    """
    Blacklists the provided refresh token to invalidate the session.
    The access token remains valid until natural expiry — client should discard it.
    """
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Authentication / Authorization"],
        operation_summary="Log out and blacklist the refresh token",
        operation_description=(
            "Invalidates the provided refresh token by adding it to the JWT blacklist. "
            "After calling this endpoint the refresh token can no longer be used to obtain new access tokens.\n\n"
            "The current access token remains technically valid until it naturally expires — "
            "the client should discard it locally on logout."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The refresh token to blacklist",
                ),
            },
            example={"refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
        ),
        responses={
            205: openapi.Response(description="Successfully logged out — refresh token blacklisted"),
            400: openapi.Response(description="Invalid or already-blacklisted refresh token"),
            401: openapi.Response(description="Not authenticated"),
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data['refresh']

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
