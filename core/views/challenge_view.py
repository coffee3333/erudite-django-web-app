from rest_framework import generics, permissions, parsers, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.serializers.challenge_serializer import ChallengeSerializer, ChallengeListSerializer
from core.models.topic_model import Topic
from core.models.challenge_model import Challenge
from core.permissions import IsTeacherUser, IsEmailVerified
from django.shortcuts import get_object_or_404

class ChallengeCreateAPIView(generics.CreateAPIView):
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser, IsEmailVerified]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @swagger_auto_schema(
        tags=["Challenge"],
        operation_summary="Create a new challenge (multipart form-data)",
        manual_parameters=[
            openapi.Parameter("topic_slug", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter("title", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter("body", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter("points", openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter("difficulty", openapi.IN_FORM, type=openapi.TYPE_STRING, enum=["easy","medium","hard"], required=True),
            openapi.Parameter(
                "answers",
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description='Repeat field: A, B, C, D.'
            ),
            openapi.Parameter("correct_answer", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True,
                              description="Must be one of answers if answers are provided."),
            openapi.Parameter("case_sensitive", openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=False),
            openapi.Parameter("photo", openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
        ],
        responses={201: ChallengeSerializer()},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)




class ChallengeListAPIView(generics.ListAPIView):
    serializer_class = ChallengeListSerializer
    permission_classes = [permissions.AllowAny]  # или IsAuthenticated — как тебе нужно

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        # 404, если топика нет
        get_object_or_404(Topic, slug=slug)
        return (
            Challenge.objects
            .filter(topic__slug=slug)
            .select_related("topic", "correct_answer")
            .prefetch_related("options")
            .order_by("id")
        )

    @swagger_auto_schema(
        tags=["Challenge"],
        operation_summary="List challenges by topic slug",
        manual_parameters=[
            openapi.Parameter(
                "slug", openapi.IN_PATH, description="Topic slug",
                type=openapi.TYPE_STRING, required=True
            )
        ],
        responses={200: ChallengeListSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)