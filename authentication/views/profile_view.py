from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from authentication.serializers import UserSerializer, UserProfileUpdateSerializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from authentication.models import User
from authentication.filters import UserFilter
from authentication.pagination import CustomPagination
from authentication.permissions import IsOwnerOrReadOnly


class MeProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve the authenticated user's profile.",
        tags=['Profile'],
        responses={200: UserSerializer}
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class MeProfileUpdateView(generics.UpdateAPIView):
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    http_method_names = ['patch']

    @swagger_auto_schema(
        operation_description="Update the authenticated user's profile (username, bio, photo).",
        tags=['Profile'],
        responses={200: UserProfileUpdateSerializer, 400: "Bad Request"}
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def get_object(self):
        return self.request.user

# class ProfileView(generics.RetrieveAPIView):
#     serializer_class = UserDetailSerializer
#     permission_classes = [AllowAny, IsOwnerOrReadOnly]
#
#     @swagger_auto_schema(
#         operation_description="Retrieve a user's profile by user ID.",
#         tags=['Profile'],
#         responses={200: UserDetailSerializer, 404: "User not found"}
#     )
#     def get(self, request, *args, **kwargs):
#         return self.retrieve(request, *args, **kwargs)
#
#     def get_object(self):
#         slug = self.kwargs.get('slug')
#         return generics.get_object_or_404(User, slug=slug)


# class ProfilesList(generics.ListAPIView):
#     queryset = User.objects.all().order_by('id')
#     serializer_class = UserSerializer
#     permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
#     pagination_class = CustomPagination
#     parser_classes = (MultiPartParser, FormParser)
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = UserFilter
#
#     @swagger_auto_schema(
#         operation_description="List all user profiles with pagination and optional filters.",
#         tags=['Profile'],
#         responses={200: UserSerializer(many=True)}
#     )
#     def get(self, request, *args, **kwargs):
#         return super().get(request, *args, **kwargs)


# class ProfileUpdateView(generics.UpdateAPIView):
#     serializer_class = UserProfileSerializer
#     permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
#     parser_classes = (MultiPartParser, FormParser)
#
#     @swagger_auto_schema(
#         operation_description="Update the authenticated user's profile.",
#         tags=['Profile'],
#         responses={200: UserProfileSerializer, 400: "Bad Request"}
#     )
#     def put(self, request, *args, **kwargs):
#         return self.update(request, *args, **kwargs)
#
#     @swagger_auto_schema(
#         operation_description="Partially update the authenticated user's profile.",
#         tags=['Profile'],
#         responses={200: UserProfileSerializer, 400: "Bad Request"}
#     )
#     def patch(self, request, *args, **kwargs):
#         return self.partial_update(request, *args, **kwargs)
#
#     def get_object(self):
#         return self.request.user
