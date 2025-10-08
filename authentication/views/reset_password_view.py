import random
from django.core.mail import send_mail
from rest_framework import generics, status
from rest_framework.response import Response
from authentication.models import User
from authentication.models import PasswordResetOTP
from authentication.serializers import RequestOTPSerializer, ConfirmOTPSerializer
from drf_yasg.utils import swagger_auto_schema


class RequestPasswordOTPView(generics.GenericAPIView):
    serializer_class = RequestOTPSerializer

    @swagger_auto_schema(
        operation_description="Request an OTP code to reset password. The code will be sent to the provided email address.",
        tags=['User Reset Password'],
        responses={
            200: "OTP has been sent to your email.",
            404: "User with this email not found.",
            400: "Bad Request: Invalid input data"
        }
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
    serializer_class = ConfirmOTPSerializer

    @swagger_auto_schema(
        operation_description="Confirm OTP and set a new password.",
        tags=['User Reset Password'],
        responses={
            200: "Password has been changed successfully.",
            400: "Invalid or expired OTP.",
            404: "User with this email not found."
        }
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
