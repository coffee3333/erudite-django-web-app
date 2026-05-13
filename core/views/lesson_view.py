# core/views/lesson_view.py
from rest_framework import generics, permissions, parsers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.models.lesson import Lesson
from core.models.topic_model import Topic
from core.permissions import IsAuthorOrReadOnly, IsTeacherUser, IsEmailVerified
from core.serializers.lesson_serializer import LessonSerializer
from core.serializers.topic_serializer import TopicDetailSerializer
from core.utils.access import user_can_access_course


class LessonCreateView(generics.CreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser, IsEmailVerified]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @swagger_auto_schema(
        tags=["Lesson"],
        operation_summary="Create a new lesson inside a topic",
        operation_description=(
            "Creates a lesson and attaches it to the topic identified by `topic_slug`. "
            "Set `sort_order` to control where this lesson appears in the topic's "
            "ordered item list relative to other lessons and challenges."
        ),
        manual_parameters=[
            openapi.Parameter(
                "topic_slug", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True,
                description="Slug of the parent topic",
            ),
            openapi.Parameter(
                "title", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True,
                description="Lesson title",
            ),
            openapi.Parameter(
                "content", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description="Markdown or HTML body text",
            ),
            openapi.Parameter(
                "video_url", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description="URL to an embedded video (YouTube, Vimeo, etc.)",
            ),
            openapi.Parameter(
                "content_type", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                enum=["text", "video", "mixed"],
                description="text = markdown only | video = video only | mixed = both",
            ),
            openapi.Parameter(
                "sort_order", openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False,
                description="Position in the topic's ordered item list (shared with challenge sort_order)",
            ),
            openapi.Parameter(
                "estimated_minutes", openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False,
                description="Estimated time to complete this lesson in minutes",
            ),
        ],
        responses={
            201: openapi.Response(description="Lesson created", schema=LessonSerializer()),
            400: openapi.Response(description="Validation error or missing topic_slug"),
            401: openapi.Response(description="Not authenticated"),
            403: openapi.Response(description="Not a teacher or email not verified"),
            404: openapi.Response(description="Topic not found"),
        },
    )
    def post(self, request, *args, **kwargs):
        topic_slug = request.data.get("topic_slug")
        if not topic_slug:
            return Response(
                {"error": "Field 'topic_slug' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        topic = get_object_or_404(Topic, slug=topic_slug)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(topic=topic, owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LessonDetailView(generics.RetrieveAPIView):
    serializer_class = LessonSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    queryset = Lesson.objects.select_related("topic", "owner")

    @swagger_auto_schema(
        tags=["Lesson"],
        operation_summary="Get lesson detail by slug",
        operation_description="Returns full lesson content. Public — no authentication required.",
        manual_parameters=[
            openapi.Parameter(
                "slug", openapi.IN_PATH, type=openapi.TYPE_STRING,
                required=True, description="Lesson slug",
            ),
        ],
        responses={
            200: openapi.Response(description="Lesson detail", schema=LessonSerializer()),
            404: openapi.Response(description="Lesson not found"),
        },
    )
    def get(self, request, *args, **kwargs):
        lesson = get_object_or_404(Lesson.objects.select_related("topic__course"), slug=self.kwargs["slug"])
        if not user_can_access_course(request.user, lesson.topic.course):
            raise PermissionDenied("You do not have access to this course.")
        serializer = self.get_serializer(lesson)
        return Response(serializer.data)


class LessonUpdateView(generics.UpdateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    lookup_field = "slug"
    http_method_names = ["patch", "head", "options"]

    def get_queryset(self):
        return Lesson.objects.select_related("owner")

    def get_object(self):
        obj = get_object_or_404(Lesson, slug=self.kwargs["slug"])
        self.check_object_permissions(self.request, obj)
        return obj

    @swagger_auto_schema(
        tags=["Lesson"],
        operation_summary="Partially update a lesson",
        operation_description=(
            "Update any subset of lesson fields. Only the lesson owner can edit it.\n\n"
            "Send a JSON body with the fields you want to change."
        ),
        manual_parameters=[
            openapi.Parameter(
                "slug", openapi.IN_PATH, type=openapi.TYPE_STRING,
                required=True, description="Lesson slug",
            ),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "title":               openapi.Schema(type=openapi.TYPE_STRING),
                "content":             openapi.Schema(type=openapi.TYPE_STRING, description="Markdown body"),
                "video_url":           openapi.Schema(type=openapi.TYPE_STRING),
                "content_type":        openapi.Schema(type=openapi.TYPE_STRING, enum=["text", "video", "mixed"]),
                "sort_order":          openapi.Schema(type=openapi.TYPE_INTEGER),
                "estimated_minutes":   openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            example={"title": "Updated title", "sort_order": 3},
        ),
        responses={
            200: openapi.Response(description="Updated lesson", schema=LessonSerializer()),
            400: openapi.Response(description="Validation error"),
            401: openapi.Response(description="Not authenticated"),
            403: openapi.Response(description="Not the lesson owner"),
            404: openapi.Response(description="Lesson not found"),
        },
    )
    def patch(self, request, *args, **kwargs):
        if request.data.get("remove_photo") == "1":
            lesson = self.get_object()
            if lesson.photo:
                lesson.photo.delete(save=False)
                lesson.photo = None
                lesson.save(update_fields=["photo"])
        return self.partial_update(request, *args, **kwargs)


class LessonDeleteView(generics.DestroyAPIView):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return Lesson.objects.select_related("owner")

    def get_object(self):
        obj = get_object_or_404(Lesson, slug=self.kwargs["slug"])
        self.check_object_permissions(self.request, obj)
        return obj

    @swagger_auto_schema(
        tags=["Lesson"],
        operation_summary="Delete a lesson by slug",
        operation_description="Permanently deletes the lesson. Only the lesson owner can do this.",
        manual_parameters=[
            openapi.Parameter(
                "slug", openapi.IN_PATH, type=openapi.TYPE_STRING,
                required=True, description="Lesson slug",
            ),
        ],
        responses={
            204: openapi.Response(description="Lesson deleted"),
            401: openapi.Response(description="Not authenticated"),
            403: openapi.Response(description="Not the lesson owner"),
            404: openapi.Response(description="Lesson not found"),
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class TopicItemsView(APIView):
    """Returns the full ordered curriculum of a topic — lessons and challenges merged by sort_order."""
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=["Topic"],
        operation_summary="Get ordered curriculum for a topic (lessons + challenges)",
        operation_description=(
            "Returns all lessons and challenges belonging to a topic, merged into a single "
            "list ordered by `sort_order`. This is the primary endpoint for rendering a "
            "topic's learning path on the frontend.\n\n"
            "Each item has a `type` field (`lesson` or `challenge`) so the frontend knows "
            "how to render it. Challenge-only fields (`challenge_type`, `points`) are `null` "
            "on lesson items, and lesson-only fields (`content_type`, `estimated_minutes`) "
            "are `null` on challenge items."
        ),
        manual_parameters=[
            openapi.Parameter(
                "slug", openapi.IN_PATH, type=openapi.TYPE_STRING,
                description="Topic slug", required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Topic with ordered items list",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id":          openapi.Schema(type=openapi.TYPE_INTEGER),
                        "slug":        openapi.Schema(type=openapi.TYPE_STRING),
                        "title":       openapi.Schema(type=openapi.TYPE_STRING),
                        "description": openapi.Schema(type=openapi.TYPE_STRING),
                        "items": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "type":               openapi.Schema(type=openapi.TYPE_STRING, enum=["lesson", "challenge"]),
                                    "slug":               openapi.Schema(type=openapi.TYPE_STRING),
                                    "title":              openapi.Schema(type=openapi.TYPE_STRING),
                                    "sort_order":         openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "challenge_type":     openapi.Schema(type=openapi.TYPE_STRING, nullable=True, enum=["quiz", "text", "code"]),
                                    "points":             openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
                                    "content_type":       openapi.Schema(type=openapi.TYPE_STRING, nullable=True, enum=["text", "video", "mixed"]),
                                    "estimated_minutes":  openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
                                },
                            ),
                        ),
                    },
                    example={
                        "id": 1,
                        "slug": "intro-to-python",
                        "title": "Intro to Python",
                        "description": "Learn the basics",
                        "items": [
                            {"type": "lesson",    "slug": "variables-explained", "title": "Variables", "sort_order": 1, "challenge_type": None, "points": None, "content_type": "text", "estimated_minutes": 5},
                            {"type": "challenge", "slug": "variables-quiz",      "title": "Variables Quiz", "sort_order": 2, "challenge_type": "quiz", "points": 10, "content_type": None, "estimated_minutes": None},
                            {"type": "challenge", "slug": "fizzbuzz",            "title": "FizzBuzz", "sort_order": 3, "challenge_type": "code", "points": 30, "content_type": None, "estimated_minutes": None},
                        ],
                    },
                ),
            ),
            404: openapi.Response(description="Topic not found"),
        },
    )
    def get(self, request, slug):
        topic = get_object_or_404(
            Topic.objects.select_related("course").prefetch_related(
                "lessons",
                "challenges",
                "challenges__submissions",
                "challenges__code_config",
            ),
            slug=slug,
        )
        if not user_can_access_course(request.user, topic.course):
            raise PermissionDenied("You do not have access to this course.")
        serializer = TopicDetailSerializer(topic, context={"request": request})
        return Response(serializer.data)
