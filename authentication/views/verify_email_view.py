import random
from django.core.mail import send_mail
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from ..models import User, EmailVerificationCode
from ..serializers import (
    RequestEmailVerificationSerializer,
    ConfirmEmailVerificationSerializer,
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RequestEmailVerificationView(generics.GenericAPIView):
    """
    Sends a 6-digit email verification code to the authenticated user.
    No-op if the email is already verified. Code is valid for 10 minutes.
    """
    serializer_class = RequestEmailVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=["User Email Verification"],
        operation_summary="Send an email verification code",
        operation_description=(
            "Generates a 6-digit verification code and emails it to the authenticated user's address.\n\n"
            "If the email is already verified, this is a no-op and returns 200 with a message.\n\n"
            "The code is valid for **10 minutes**. Pass it to "
            "`POST /api/users/users/me/email/verify/confirm/` to complete verification.\n\n"
            "A verified email is required to submit challenge answers and create course content."
        ),
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={}),
        responses={
            200: openapi.Response(
                description="Verification code sent (or email already verified)",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING, example="Verification code sent to email.")},
                ),
            ),
            401: openapi.Response(description="Not authenticated"),
        },
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        if user.email_verified:
            return Response({'message': 'Email is already verified.'}, status=status.HTTP_200_OK)
        code = f"{random.randint(100000, 999999)}"
        EmailVerificationCode.objects.create(user=user, code=code)
        send_mail(
            'Email verification code',
            f'Your verification code is: {code}',
            None,
            [user.email],
        )
        return Response({'message': 'Verification code sent to email.'}, status=status.HTTP_200_OK)


class ConfirmEmailVerificationView(generics.GenericAPIView):
    """
    Confirms the 6-digit verification code and marks the user's email as verified.
    A verified email is required to submit challenges and create course content.
    """
    serializer_class = ConfirmEmailVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=["User Email Verification"],
        operation_summary="Confirm the verification code",
        operation_description=(
            "Verifies the 6-digit code sent to the user's email and marks the account as email-verified.\n\n"
            "The code expires after **10 minutes** and can only be used once. "
            "Request a new code via `POST /api/users/users/me/email/verify/request/` if it has expired."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["code"],
            properties={
                "code": openapi.Schema(type=openapi.TYPE_STRING, description="6-digit verification code received by email"),
            },
            example={"code": "391847"},
        ),
        responses={
            200: openapi.Response(
                description="Email successfully verified",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING, example="Email successfully verified.")},
                ),
            ),
            400: openapi.Response(description="Invalid or expired verification code"),
            401: openapi.Response(description="Not authenticated"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']
        user = request.user
        code_obj = EmailVerificationCode.objects.filter(user=user, code=code, is_used=False).order_by('-created_at').first()
        if not code_obj or not code_obj.is_valid():
            return Response({'error': 'Invalid or expired verification code.'}, status=status.HTTP_400_BAD_REQUEST)
        code_obj.is_used = True
        code_obj.save()
        user.email_verified = True
        user.save()
        return Response({'message': 'Email successfully verified.'}, status=status.HTTP_200_OK)

