import random
from django.core.mail import send_mail
from rest_framework import generics, status
from rest_framework.response import Response
from ..models import User, EmailVerificationCode
from ..serializers import (
    RequestEmailVerificationSerializer,
    ConfirmEmailVerificationSerializer,
)
from drf_yasg.utils import swagger_auto_schema


class RequestEmailVerificationView(generics.GenericAPIView):
    serializer_class = RequestEmailVerificationSerializer

    @swagger_auto_schema(
        operation_description="Request an email verification code. The code will be sent to the provided email address.",
        tags=['User Email Verification'],
        responses={
            200: "Verification code sent to email.",
            404: "User with this email does not exist.",
            400: "Bad Request: Invalid input data"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        code = f"{random.randint(100000, 999999)}"
        EmailVerificationCode.objects.create(user=user, code=code)
        send_mail(
            'Email verification code',
            f'Your verification code is: {code}',
            None,
            [email],
        )
        return Response({'message': 'Verification code sent to email.'}, status=status.HTTP_200_OK)


class ConfirmEmailVerificationView(generics.GenericAPIView):
    serializer_class = ConfirmEmailVerificationSerializer

    @swagger_auto_schema(
        operation_description="Confirm the email verification code to verify the user's email address.",
        tags=['User Email Verification'],
        responses={
            200: "Email successfully verified.",
            400: "Invalid or expired verification code.",
            404: "User with this email does not exist."
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        code_obj = EmailVerificationCode.objects.filter(user=user, code=code, is_used=False).order_by('-created_at').first()
        if not code_obj or not code_obj.is_valid():
            return Response({'error': 'Invalid or expired verification code.'}, status=status.HTTP_400_BAD_REQUEST)
        code_obj.is_used = True
        code_obj.save()
        user.email_verified = True
        user.save()
        return Response({'message': 'Email successfully verified.'}, status=status.HTTP_200_OK)
