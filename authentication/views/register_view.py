from rest_framework import generics, permissions, status
from ..serializers import UserRegisterSerializer, UserSerializer
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(
        operation_description="Register a new user.",
        tags=['Authentication / Authorization'],
        responses={
            201: openapi.Response(
                description="User created successfully",
                schema=UserSerializer
            ),
            400: "Bad Request: Invalid input data"
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Register a new user.
        """
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
