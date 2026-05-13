from rest_framework import permissions, status
from core.permissions import IsEmailVerified
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.models.challenge_model import Challenge
from core.models.challenge_correct_answer import ChallengeCorrectAnswer
from core.models.submission_model import Submission
from core.utils.completion import check_and_issue_certificate


class ChallengeAnswerCheckAPIView(APIView):
    """
    Quick answer check for quiz and text challenges.
    Saves a Submission with status 'passed' or 'failed' and returns the result immediately.
    Only works for quiz and text challenges (not code — use /run/ and /submit/ for those).
    """
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]
    parser_classes = [JSONParser]

    @swagger_auto_schema(
        tags=["Challenge"],
        operation_summary="Check an answer and record a submission (quiz / text)",
        operation_description=(
            "Checks the provided answer, saves a `Submission` record with `status='passed'` "
            "or `status='failed'`, and awards points on a correct answer.\n\n"
            "Only valid for `quiz` and `text` challenge types.\n\n"
            "**Quiz:** send the option text string (same value as shown in the `options` list).\n\n"
            "**Text:** send the free-text answer string.\n\n"
            "Use `POST /challenges/<slug>/submit/` if you want to pass `option_id` for quiz "
            "challenges or execute code for code challenges."
        ),
        manual_parameters=[
            openapi.Parameter(
                "slug", openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                description="Challenge slug",
                required=True,
            ),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["answer"],
            properties={
                "answer": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The answer string to check",
                ),
            },
            example={"answer": "Paris"},
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "correct": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "score":   openapi.Schema(type=openapi.TYPE_INTEGER, description="Points earned"),
                },
                example={"correct": True, "score": 10},
            ),
            400: openapi.Response(description="Missing 'answer' field or not a quiz/text challenge"),
            401: openapi.Response(description="Not authenticated"),
            404: openapi.Response(description="Challenge or correct answer not found"),
        },
    )
    def post(self, request, slug):
        challenge = get_object_or_404(
            Challenge.objects.select_related("correct_answer", "topic__course"),
            slug=slug,
        )

        if challenge.challenge_type == "code":
            return Response(
                {"detail": "Use /run/ to test code and /submit/ to submit it."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        correct_obj = getattr(challenge, "correct_answer", None)
        if correct_obj is None:
            return Response(
                {"detail": "Correct answer is not configured for this challenge."},
                status=status.HTTP_404_NOT_FOUND,
            )

        provided = request.data.get("answer")
        if provided is None:
            return Response(
                {"detail": "Field 'answer' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        provided = str(provided).strip()
        expected = correct_obj.correct_answer.strip()

        if correct_obj.case_sensitive:
            is_correct = provided == expected
        else:
            is_correct = provided.lower() == expected.lower()

        earned = challenge.points if is_correct else 0

        # Compute next attempt number
        last = (
            Submission.objects.filter(user=request.user, challenge=challenge)
            .order_by("-attempt_no")
            .values_list("attempt_no", flat=True)
            .first()
        )
        attempt_no = (last or 0) + 1

        Submission.objects.create(
            user=request.user,
            challenge=challenge,
            attempt_no=attempt_no,
            answer_text=provided,
            status="passed" if is_correct else "failed",
            score=earned,
            graded_at=timezone.now(),
        )

        cert = check_and_issue_certificate(request.user, challenge.topic.course) if is_correct else None
        return Response({"correct": is_correct, "score": earned, "certificate_issued": cert is not None}, status=status.HTTP_200_OK)
