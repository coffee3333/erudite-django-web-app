from rest_framework import generics, permissions, parsers, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.serializers.challenge_serializer import (
    ChallengeSerializer, ChallengeListSerializer, ChallengeCreateSerializer,
)
from core.models.topic_model import Topic
from core.models.challenge_model import Challenge
from core.models.submission_model import Submission
from core.permissions import IsTeacherUser, IsEmailVerified
from core.utils.access import user_can_access_course
from django.shortcuts import get_object_or_404


class ChallengeCreateAPIView(generics.CreateAPIView):
    """
    Creates a quiz or text challenge (multipart form).
    For code challenges use ChallengeCreateView (JSON).
    """
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser, IsEmailVerified]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @swagger_auto_schema(
        tags=["Challenge"],
        operation_summary="Create a quiz or text challenge",
        operation_description=(
            "Creates a **quiz** or **text** challenge and attaches it to a topic.\n\n"
            "**Quiz challenge** — provide `answers` as a comma-separated list and set "
            "`correct_answer` to one of those values. The student will see the options "
            "as radio buttons and submit an `option_id`.\n\n"
            "**Text challenge** — leave `answers` empty. The student types a free-text "
            "answer which is compared against `correct_answer` (optionally case-sensitive).\n\n"
            "For **code challenges** use `POST /api/platform/challenge/create-code/` which "
            "accepts JSON with nested test cases."
        ),
        manual_parameters=[
            openapi.Parameter(
                "topic_slug", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True,
                description="Slug of the parent topic",
            ),
            openapi.Parameter(
                "title", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True,
                description="Challenge title",
            ),
            openapi.Parameter(
                "body", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True,
                description="The question or problem statement shown to the student",
            ),
            openapi.Parameter(
                "points", openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=True,
                description="Points awarded for a correct answer",
            ),
            openapi.Parameter(
                "difficulty", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True,
                enum=["easy", "medium", "hard"],
            ),
            openapi.Parameter(
                "answers", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description=(
                    "Comma-separated list of options for quiz challenges. "
                    "Example: `Paris,London,Berlin,Madrid`. "
                    "Leave empty for text challenges."
                ),
            ),
            openapi.Parameter(
                "correct_answer", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True,
                description=(
                    "The correct answer. Must exactly match one of the `answers` values "
                    "(respecting `case_sensitive`) when answers are provided."
                ),
            ),
            openapi.Parameter(
                "case_sensitive", openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False,
                description="Whether answer comparison is case-sensitive. Default: false.",
            ),
            openapi.Parameter(
                "photo", openapi.IN_FORM, type=openapi.TYPE_FILE, required=False,
                description="Optional image attachment for the challenge",
            ),
        ],
        responses={
            201: openapi.Response(description="Challenge created", schema=ChallengeSerializer()),
            400: openapi.Response(description="Validation error (e.g. correct_answer not in answers list)"),
            401: openapi.Response(description="Not authenticated"),
            403: openapi.Response(description="Not a teacher or email not verified"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChallengeListAPIView(generics.ListAPIView):
    serializer_class = ChallengeListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        topic = get_object_or_404(Topic.objects.select_related("course"), slug=slug)
        if not user_can_access_course(self.request.user, topic.course):
            raise PermissionDenied("You do not have access to this course.")
        return (
            Challenge.objects
            .filter(topic=topic)
            .select_related("topic", "correct_answer", "code_config")
            .prefetch_related("options", "submissions")
            .order_by("sort_order", "id")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @swagger_auto_schema(
        tags=["Challenge"],
        operation_summary="List all challenges for a topic",
        operation_description=(
            "Returns all challenges belonging to the given topic slug, ordered by `sort_order`. "
            "Each challenge includes its multiple-choice options list (empty for text/code challenges). "
            "Public — no authentication required."
        ),
        manual_parameters=[
            openapi.Parameter(
                "slug", openapi.IN_PATH, type=openapi.TYPE_STRING,
                description="Topic slug", required=True,
            ),
        ],
        responses={
            200: openapi.Response(description="List of challenges", schema=ChallengeListSerializer(many=True)),
            404: openapi.Response(description="Topic not found"),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ChallengeCreateView(generics.CreateAPIView):
    """
    Creates a code challenge with nested CodeChallengeConfig and test cases.
    Accepts JSON (not multipart).
    """
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser, IsEmailVerified]
    parser_classes = [parsers.JSONParser]
    serializer_class = ChallengeCreateSerializer

    @swagger_auto_schema(
        tags=["Challenge"],
        operation_summary="Create a code challenge with test cases (JSON)",
        operation_description=(
            "Creates a **code** challenge with an attached execution config and test cases.\n\n"
            "The student's code is executed against each test case in a sandboxed process. "
            "Set `is_public: true` on test cases you want students to see as examples; "
            "hidden test cases only reveal pass/fail, not stdout.\n\n"
            "**Supported languages:** `python`, `javascript`, `java`, `cpp`\n\n"
            "The `solution_template` is shown to the student as starter code in the editor. "
            "The `solution_hidden` is the reference solution — it is never sent to the client."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["topic", "title", "body", "difficulty", "points", "challenge_type", "code_config"],
            properties={
                "topic":           openapi.Schema(type=openapi.TYPE_INTEGER, description="Topic ID (use GET /topics/<slug>/ to find the id)"),
                "title":           openapi.Schema(type=openapi.TYPE_STRING),
                "body":            openapi.Schema(type=openapi.TYPE_STRING, description="Problem statement shown to the student"),
                "difficulty":      openapi.Schema(type=openapi.TYPE_STRING, enum=["easy", "medium", "hard"]),
                "points":          openapi.Schema(type=openapi.TYPE_INTEGER),
                "challenge_type":  openapi.Schema(type=openapi.TYPE_STRING, enum=["code"], description="Must be 'code' for this endpoint"),
                "code_config": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    required=["language", "test_cases"],
                    properties={
                        "language":           openapi.Schema(type=openapi.TYPE_STRING, enum=["python", "javascript", "java", "cpp"]),
                        "solution_template":  openapi.Schema(type=openapi.TYPE_STRING, description="Starter code shown to student in editor"),
                        "solution_hidden":    openapi.Schema(type=openapi.TYPE_STRING, description="Reference solution — never sent to client"),
                        "time_limit_seconds": openapi.Schema(type=openapi.TYPE_INTEGER, description="Per-test-case CPU time limit. Default: 5"),
                        "memory_limit_mb":    openapi.Schema(type=openapi.TYPE_INTEGER, description="Memory limit in MB. Default: 128"),
                        "test_cases": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                required=["expected_stdout"],
                                properties={
                                    "stdin":           openapi.Schema(type=openapi.TYPE_STRING, description="Input piped to the program via stdin"),
                                    "expected_stdout": openapi.Schema(type=openapi.TYPE_STRING, description="Expected program output (trimmed before comparison)"),
                                    "is_public":       openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Show this test case to students as an example. Default: false"),
                                    "weight":          openapi.Schema(type=openapi.TYPE_NUMBER, description="Scoring weight for partial credit. Default: 1.0"),
                                    "description":     openapi.Schema(type=openapi.TYPE_STRING, description="Internal label e.g. 'Edge case: empty input'"),
                                },
                            ),
                        ),
                    },
                ),
            },
            example={
                "topic": 1,
                "title": "Double the number",
                "body": "Read an integer from stdin and print it doubled.",
                "difficulty": "easy",
                "points": 20,
                "challenge_type": "code",
                "code_config": {
                    "language": "python",
                    "solution_template": "import sys\n\ndef solution(n):\n    # write your code here\n    pass\n\nprint(solution(int(sys.stdin.read().strip())))",
                    "solution_hidden": "import sys\nprint(int(sys.stdin.read().strip()) * 2)",
                    "time_limit_seconds": 5,
                    "memory_limit_mb": 128,
                    "test_cases": [
                        {"stdin": "4",  "expected_stdout": "8",  "is_public": True,  "weight": 1.0, "description": "Basic case"},
                        {"stdin": "0",  "expected_stdout": "0",  "is_public": False, "weight": 1.0, "description": "Zero"},
                        {"stdin": "-3", "expected_stdout": "-6", "is_public": False, "weight": 1.0, "description": "Negative number"},
                    ],
                },
            },
        ),
        responses={
            201: openapi.Response(description="Code challenge created"),
            400: openapi.Response(description="Validation error — e.g. challenge_type is not 'code' but code_config provided"),
            401: openapi.Response(description="Not authenticated"),
            403: openapi.Response(description="Not a teacher or email not verified"),
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UseHintView(APIView):
    """POST /platform/challenges/<slug>/use-hint/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        challenge = get_object_or_404(Challenge, slug=slug)
        if not challenge.hint:
            return Response({"detail": "No hint available."}, status=status.HTTP_404_NOT_FOUND)

        # Get or create latest submission to track hint_used
        sub = Submission.objects.filter(challenge=challenge, user=request.user).first()
        if sub and not sub.hint_used:
            sub.hint_used = True
            sub.save(update_fields=["hint_used"])

        return Response({"hint": challenge.hint})


class RevealSolutionView(APIView):
    """POST /platform/challenges/<slug>/reveal-solution/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        challenge = get_object_or_404(Challenge, slug=slug)
        if not challenge.solution_explanation:
            return Response({"detail": "No solution available."}, status=status.HTTP_404_NOT_FOUND)

        # Always ensure a submission row exists and mark solution_revealed=True
        # so the submit endpoint can reliably block further attempts.
        sub = Submission.objects.filter(challenge=challenge, user=request.user).first()
        if sub:
            if not sub.solution_revealed:
                sub.solution_revealed = True
                sub.save(update_fields=["solution_revealed"])
        else:
            # No prior attempt — create a sentinel row so the block fires on submit
            last_attempt = (
                Submission.objects
                .filter(user=request.user, challenge=challenge)
                .order_by("-attempt_no")
                .values_list("attempt_no", flat=True)
                .first()
            )
            Submission.objects.create(
                user=request.user,
                challenge=challenge,
                attempt_no=(last_attempt or 0) + 1,
                answer_text="",
                status="failed",
                score=0,
                solution_revealed=True,
            )

        return Response({"solution_explanation": challenge.solution_explanation})
