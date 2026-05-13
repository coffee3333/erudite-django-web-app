from rest_framework import generics, permissions, status, parsers
from ..serializers import UserRegisterSerializer, UserSerializer
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RegisterView(generics.CreateAPIView):
    """
    Creates a new user account (student or teacher role).
    The account is immediately active but email is unverified until the user
    completes the email verification flow.
    """
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)

    @swagger_auto_schema(
        tags=["Authentication / Authorization"],
        operation_summary="Register a new user account",
        operation_description=(
            "Creates a new user account. Both **student** and **teacher** roles are supported.\n\n"
            "After registration the account is immediately active but **email is not verified**. "
            "Some actions (submitting challenges, creating content) require a verified email — "
            "call `POST /api/users/users/me/email/verify/request/` to trigger the verification flow.\n\n"
            "Passwords are validated against Django's default rules (minimum length, not too common, etc.)."
        ),
        manual_parameters=[
            openapi.Parameter("email",    openapi.IN_FORM, type=openapi.TYPE_STRING,  required=True,  description="Unique email address"),
            openapi.Parameter("username", openapi.IN_FORM, type=openapi.TYPE_STRING,  required=True,  description="Unique display name (max 50 chars)"),
            openapi.Parameter("password", openapi.IN_FORM, type=openapi.TYPE_STRING,  required=True,  description="Password — must meet Django password validation rules"),
            openapi.Parameter("password2",openapi.IN_FORM, type=openapi.TYPE_STRING,  required=True,  description="Password confirmation — must match password"),
            openapi.Parameter("role",     openapi.IN_FORM, type=openapi.TYPE_STRING,  required=False, description="Account role: `student` (default) or `teacher`", enum=["student", "teacher"]),
            openapi.Parameter("user_bio", openapi.IN_FORM, type=openapi.TYPE_STRING,  required=False, description="Short bio (max 255 chars)"),
            openapi.Parameter("photo",    openapi.IN_FORM, type=openapi.TYPE_FILE,    required=False, description="Profile photo (JPEG/PNG, max 5 MB)"),
        ],
        responses={
            201: openapi.Response(
                description="User created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user":    openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Serialized user object",
                            properties={
                                "id":             openapi.Schema(type=openapi.TYPE_INTEGER),
                                "username":       openapi.Schema(type=openapi.TYPE_STRING),
                                "email":          openapi.Schema(type=openapi.TYPE_STRING),
                                "role":           openapi.Schema(type=openapi.TYPE_STRING, enum=["student", "teacher"]),
                                "email_verified": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                "slug":           openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="The registration has been completed successfully."),
                    },
                ),
            ),
            400: openapi.Response(description="Validation error — duplicate email/username, password mismatch, or invalid role"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "user": UserSerializer(user).data,
                "message": "The registration has been completed successfully.",
            },
            status=status.HTTP_201_CREATED
        )
