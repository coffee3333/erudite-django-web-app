from rest_framework import permissions, parsers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.models.challenge_model import Challenge
from core.models.challenge_correct_answer import ChallengeCorrectAnswer

class ChallengeAnswerCheckAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]  # или IsAuthenticated — как нужно
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @swagger_auto_schema(
        tags=["Challenge"],
        operation_summary="Check if provided answer is correct (by challenge slug)",
        manual_parameters=[
            openapi.Parameter(
                "slug",
                openapi.IN_PATH,
                description="Challenge slug",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "answer",
                openapi.IN_FORM,
                description="User answer (string)",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "correct": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                },
                required=["correct"],
            ),
            404: "Challenge or correct answer not found",
            400: "Bad request",
        },
    )
    def post(self, request, slug):
        # 1) challenge + correct answer
        challenge = get_object_or_404(
            Challenge.objects.select_related("correct_answer"),
            slug=slug
        )
        if not hasattr(challenge, "correct_answer") or challenge.correct_answer is None:
            return Response(
                {"detail": "Correct answer is not configured for this challenge."},
                status=status.HTTP_404_NOT_FOUND,
            )

        provided = request.data.get("answer")
        if provided is None:
            return Response(
                {"error": "Field 'answer' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        provided = str(provided).strip()
        correct_obj: ChallengeCorrectAnswer = challenge.correct_answer
        expected = correct_obj.correct_answer.strip()
        case_sensitive = bool(correct_obj.case_sensitive)

        # 2) compare with/without case sensitivity
        if not case_sensitive:
            is_correct = provided.lower() == expected.lower()
        else:
            is_correct = provided == expected

        return Response({"correct": bool(is_correct)}, status=status.HTTP_200_OK)
