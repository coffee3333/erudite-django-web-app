from pydoc_data.topics import topics

from allauth.idp.oidc.views import token
from django.core.validators import slug_re
from rest_framework import generics, permissions, status, parsers
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.models.course_model import Course
from core.models.topic_model import Topic
from core.models.challenge_model import Challenge
from core.permissions import IsAuthorOrReadOnly, IsTeacherUser, IsEmailVerified
from core.serializers.topic_serializer import TopicSerializer


class TopicListAPIView(generics.ListAPIView):
    serializer_class = TopicSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        course_slug = self.kwargs.get("slug")
        get_object_or_404(Course, slug=course_slug)
        return (
            Topic.objects
            .filter(course__slug=course_slug)
            .select_related("course")
            .prefetch_related("challenges")
            .order_by("sort_order")
        )

    @swagger_auto_schema(
        tags=["Topic"],
        operation_summary="List all topics for a given course",
        responses={200: TopicSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class TopicCreateAPIView(generics.CreateAPIView):
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser, IsEmailVerified]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @swagger_auto_schema(
        tags=["Topic"],
        operation_summary="Create a new topic for a given course",
        manual_parameters=[
            openapi.Parameter(
                "title",
                openapi.IN_FORM,
                description="Topic title",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "course_slug",
                openapi.IN_FORM,
                description="Slug of the course to attach the topic",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        responses={201: TopicSerializer()},
    )

    def post(self, request, *args, **kwargs):
        course_slug = request.data.get("course_slug")
        if not course_slug:
            return Response(
                {"error": "Field 'course_slug' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        course = get_object_or_404(Course, slug=course_slug)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course, owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TopicDeleteAPIView(generics.DestroyAPIView):
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser, IsEmailVerified, IsAuthorOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return Topic.objects.select_related("course").filter(owner=self.request.user)

    @swagger_auto_schema(
        tags=["Topic"],
        operation_summary="Delete topic and all related challenges (by topic slug)",
        responses={204: "Topic and challenges deleted"},
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def perform_destroy(self, instance):
        Challenge.objects.filter(topic=instance).delete()
        instance.delete()

class TopicUpdateAPIView(generics.UpdateAPIView):
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly, IsTeacherUser, IsEmailVerified]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    http_method_names = ["patch", "head", "options"]
    lookup_field = "slug"

    @swagger_auto_schema(
        tags=["Topic"],
        operation_summary="Update topic title (by topic slug)",
        manual_parameters=[
            openapi.Parameter(
                "slug",
                openapi.IN_PATH,
                description="Slug of the topic to update",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "title",
                openapi.IN_FORM,
                description="New topic title",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        responses={200: TopicSerializer()},
    )
    def patch(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        new_title = request.data.get("title")

        if not new_title:
            return Response(
                {"error": "Query parameter 'title' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not slug:
            return Response(
                {"error": "Slug is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        topic = get_object_or_404(Topic, slug=slug)
        topic.title = new_title
        topic.save(update_fields=["title"])
        return Response(TopicSerializer(topic).data, status=status.HTTP_200_OK)
