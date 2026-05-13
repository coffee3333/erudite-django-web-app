import random
from django.core.mail import send_mail
from rest_framework import generics, status
from rest_framework.response import Response
from authentication.models import User
from authentication.models import PasswordResetOTP
from authentication.serializers import RequestOTPSerializer, ConfirmOTPSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RequestPasswordOTPView(generics.GenericAPIView):
    """
    Sends a 6-digit OTP to the user's registered email address.
    The OTP is valid for 10 minutes and is consumed by ConfirmPasswordOTPView.
    """
    serializer_class = RequestOTPSerializer

    @swagger_auto_schema(
        tags=["Authentication / Authorization"],
        operation_summary="Request a password-reset OTP",
        operation_description=(
            "Sends a 6-digit one-time password (OTP) to the provided email address.\n\n"
            "The OTP is valid for **10 minutes**. Once received, pass it along with a new "
            "password to `POST /api/users/auth/password/reset/confirm/`.\n\n"
            "If the email does not belong to any registered account a 404 is returned — "
            "this is intentional to help identify typos."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Email address of the account to reset"),
            },
            example={"email": "student@example.com"},
        ),
        responses={
            200: openapi.Response(
                description="OTP sent to the email address",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING, example="OTP has been sent to your email.")},
                ),
            ),
            400: openapi.Response(description="Validation error — invalid email format"),
            404: openapi.Response(description="No account found with that email address"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'User with this email not found.'}, status=status.HTTP_404_NOT_FOUND)
        otp_code = f"{random.randint(100000, 999999)}"
        PasswordResetOTP.objects.create(user=user, otp_code=otp_code)
        send_mail(
            'Your password reset code',
            f'Your OTP code is: {otp_code}',
            None,
            [email]
        )
        return Response({'message': 'OTP has been sent to your email.'})


class ConfirmPasswordOTPView(generics.GenericAPIView):
    """
    Verifies the OTP received by email and sets a new password.
    The OTP is single-use and expires after 10 minutes.
    """
    serializer_class = ConfirmOTPSerializer

    @swagger_auto_schema(
        tags=["Authentication / Authorization"],
        operation_summary="Confirm OTP and set a new password",
        operation_description=(
            "Verifies the 6-digit OTP and sets a new password for the account.\n\n"
            "The OTP expires after **10 minutes** and can only be used once. "
            "Request a new one via `POST /api/users/auth/password/reset/request/` if needed.\n\n"
            "The new password must pass Django's password validation rules."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "otp_code", "new_password"],
            properties={
                "email":        openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Email address of the account"),
                "otp_code":     openapi.Schema(type=openapi.TYPE_STRING, description="6-digit OTP received by email"),
                "new_password": openapi.Schema(type=openapi.TYPE_STRING, format="password", description="New password to set"),
            },
            example={"email": "student@example.com", "otp_code": "482910", "new_password": "NewStr0ngPass!"},
        ),
        responses={
            200: openapi.Response(
                description="Password changed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING, example="Password has been changed successfully.")},
                ),
            ),
            400: openapi.Response(description="Invalid or expired OTP, or new password fails validation"),
            404: openapi.Response(description="No account found with that email address"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        new_password = serializer.validated_data['new_password']

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'User with this email not found.'}, status=status.HTTP_404_NOT_FOUND)
        otp = PasswordResetOTP.objects.filter(user=user, otp_code=otp_code, is_used=False).order_by('-created_at').first()
        if not otp or not otp.is_valid():
            return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        otp.is_used = True
        otp.save()
        return Response({'message': 'Password has been changed successfully.'})
