# core/views/submission_view.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsEmailVerified
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.execution.executor import run_code_challenge
from core.models.challenge_model import Challenge
from core.models.challenge_option import ChallengeOption
from core.models.code_challenge import CodeSubmissionResult
from core.models.submission_model import Submission
from core.utils.completion import check_and_issue_certificate
from core.patterns.grader_factory import GraderFactory


def _ensure_enrolled(user, course):
    """Auto-enroll user in a private course if not already enrolled."""
    if course.status == "private" and course.owner != user:
        from core.models.enrollment_model import CourseEnrollment
        CourseEnrollment.objects.get_or_create(course=course, student=user)


def _trigger_grade_passback(user, course, score_0_to_1: float):
    """Fire LTI grade passback if the user has an active LTI session for this course."""
    try:
        from lti.models import LTISession
        from lti.tasks import send_grade_to_platform
        session = LTISession.objects.filter(
            user=user,
            resource_mapping__course=course,
        ).order_by("-created_at").first()
        if session:
            send_grade_to_platform.delay(str(session.id), score_0_to_1)
    except Exception:
        pass  # never let grade passback break the submission response

# ── Reusable response schemas ────────────────────────────────────────────────

_quiz_text_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "correct": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Whether the answer was correct"),
        "score":   openapi.Schema(type=openapi.TYPE_INTEGER, description="Points earned"),
    },
    required=["correct", "score"],
)

_test_result_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "status":   openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=["accepted", "wrong_answer", "time_limit", "memory_limit", "runtime_error", "compilation_error"],
            description="Result of this test case",
        ),
        "time_ms":  openapi.Schema(type=openapi.TYPE_NUMBER,  description="Execution time in milliseconds"),
        "stdout":   openapi.Schema(type=openapi.TYPE_STRING,  description="Program output (null for hidden test cases)", nullable=True),
        "stderr":   openapi.Schema(type=openapi.TYPE_STRING,  description="Error output (null for hidden test cases)", nullable=True),
    },
    required=["status", "time_ms"],
)

_code_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "submission_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the saved submission"),
        "status":        openapi.Schema(
            type=openapi.TYPE_STRING,
            enum=["accepted", "wrong_answer"],
            description="'accepted' only when ALL test cases pass",
        ),
        "score":   openapi.Schema(type=openapi.TYPE_INTEGER, description="Points earned based on passed test weights"),
        "passed":  openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of test cases passed"),
        "total":   openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of test cases"),
        "results": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=_test_result_schema,
            description="Per-test-case breakdown. stdout/stderr are null for hidden test cases.",
        ),
    },
    required=["submission_id", "status", "score", "passed", "total", "results"],
)


class SubmitChallengeView(APIView):
    """
    Unified submission endpoint. Behaviour depends on the challenge type:

    **quiz** — student picks one of the multiple-choice options:
    ```json
    { "option_id": 3 }
    ```

    **text** — student types a free-text answer:
    ```json
    { "answer": "photosynthesis" }
    ```

    **code** — student submits source code. The server runs it against every
    test case in a sandboxed process and returns per-test results:
    ```json
    { "code": "def solution(n):\\n    return n * 2", "language": "python" }
    ```
    `language` is optional — defaults to the language configured on the challenge.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified]
    parser_classes = [parsers.JSONParser]

    @swagger_auto_schema(
        tags=["Challenge"],
        operation_summary="Submit an answer for a challenge (quiz / text / code)",
        operation_description=(
            "Behaviour depends on `challenge_type`:\n\n"
            "**quiz** — send `{ \"option_id\": <int> }`\n\n"
            "**text** — send `{ \"answer\": \"<your answer>\" }`\n\n"
            "**code** — send `{ \"code\": \"<source code>\", \"language\": \"python\" }`\n\n"
            "The `language` field is optional for code challenges — it defaults to the "
            "language configured on the challenge. Supported values: "
            "`python`, `javascript`, `java`, `cpp`.\n\n"
            "For code challenges the server executes the code against every test case "
            "in an isolated sandbox. Public test cases show their stdout/stderr in the "
            "response; hidden test cases return `null` for those fields."
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
            description=(
                "Send **one** of the three shapes depending on `challenge_type`."
            ),
            properties={
                "option_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="[quiz only] ID of the chosen option",
                ),
                "answer": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="[text only] Free-text answer string",
                ),
                "code": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=(
                        "[code only] Full source code to execute.\n\n"
                        "**Python example:**\n"
                        "```python\n"
                        "def solution(n):\n"
                        "    return n * 2\n\n"
                        "import sys\n"
                        "print(solution(int(sys.stdin.read())))\n"
                        "```\n\n"
                        "**JavaScript example:**\n"
                        "```javascript\n"
                        "const lines = require('fs').readFileSync('/dev/stdin','utf8').trim();\n"
                        "console.log(parseInt(lines) * 2);\n"
                        "```"
                    ),
                ),
                "language": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["python", "javascript", "java", "cpp"],
                    description="[code only] Override the challenge language. Optional.",
                ),
            },
            example={
                "code": "import sys\nprint(int(sys.stdin.read().strip()) * 2)",
                "language": "python",
            },
        ),
        responses={
            200: openapi.Response(
                description=(
                    "**quiz / text:** `{ correct, score }`\n\n"
                    "**code:** `{ submission_id, status, score, passed, total, results[] }`"
                ),
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Shape depends on challenge_type (see above)",
                ),
                examples={
                    "application/json (quiz/text)": {
                        "correct": True,
                        "score": 10,
                    },
                    "application/json (code)": {
                        "submission_id": 42,
                        "status": "accepted",
                        "score": 30,
                        "passed": 3,
                        "total": 3,
                        "results": [
                            {"status": "accepted",     "time_ms": 12.4, "stdout": "4",  "stderr": ""},
                            {"status": "accepted",     "time_ms": 9.1,  "stdout": None, "stderr": None},
                            {"status": "wrong_answer", "time_ms": 8.7,  "stdout": None, "stderr": None},
                        ],
                    },
                },
            ),
            400: openapi.Response(description="Missing required field for the challenge type"),
            401: openapi.Response(description="Not authenticated"),
            404: openapi.Response(description="Challenge / option / correct answer not found"),
        },
    )
    def post(self, request, slug):
        challenge = get_object_or_404(
            Challenge.objects.select_related("correct_answer", "code_config", "topic__course"),
            slug=slug,
        )

        _ensure_enrolled(request.user, challenge.topic.course)

        # Block submission if student already revealed the solution
        if challenge.solution_explanation:
            already_revealed = Submission.objects.filter(
                user=request.user, challenge=challenge, solution_revealed=True
            ).exists()
            if already_revealed:
                return Response(
                    {"detail": "You have already revealed the solution and cannot submit this challenge anymore."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        grader_key = GraderFactory.resolve(challenge.challenge_type, challenge)
        if grader_key == "quiz_mcq":
            return self._grade_quiz(request, challenge)
        if grader_key == "text" or grader_key == "quiz_text":
            return self._grade_text(request, challenge)
        if grader_key == "code":
            return self._grade_code(request, challenge)
        return Response(
            {"detail": f"Unknown challenge type: {challenge.challenge_type}"},
            status=status.HTTP_400_BAD_REQUEST,
        )



    def _next_attempt_no(self, user, challenge):
        last = (
            Submission.objects.filter(user=user, challenge=challenge)
            .order_by("-attempt_no")
            .values_list("attempt_no", flat=True)
            .first()
        )
        return (last or 0) + 1

    # ── Quiz (MCQ) ──────────────────────────────────────────────────────────
    def _grade_quiz(self, request, challenge):
        option_id = request.data.get("option_id")
        if not option_id:
            return Response(
                {"detail": "Field 'option_id' is required for quiz challenges."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            option = challenge.options.get(id=option_id)
        except ChallengeOption.DoesNotExist:
            return Response(
                {"detail": "Option not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        correct_obj = getattr(challenge, "correct_answer", None)
        if correct_obj is None:
            return Response(
                {"detail": "Correct answer not configured for this challenge."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if correct_obj.case_sensitive:
            is_correct = option.text.strip() == correct_obj.correct_answer.strip()
        else:
            is_correct = option.text.strip().lower() == correct_obj.correct_answer.strip().lower()

        hint_used = bool(request.data.get("hint_used", False))
        if is_correct:
            earned = round(challenge.points * 0.5) if hint_used else challenge.points
        else:
            earned = 0

        Submission.objects.create(
            user=request.user,
            challenge=challenge,
            attempt_no=self._next_attempt_no(request.user, challenge),
            answer_text=str(option_id),
            status="passed" if is_correct else "failed",
            score=earned,
            hint_used=hint_used,
            graded_at=timezone.now(),
        )
        cert, score_changed = check_and_issue_certificate(request.user, challenge.topic.course) if is_correct else (None, False)
        if cert and score_changed:
            _trigger_grade_passback(request.user, challenge.topic.course, cert.score_pct / 100)
        return Response({"correct": is_correct, "score": earned, "certificate_issued": cert is not None})

    # ── Text match ──────────────────────────────────────────────────────────
    def _grade_text(self, request, challenge):
        answer = str(request.data.get("answer", "")).strip()
        if not answer:
            return Response(
                {"detail": "Field 'answer' is required for text challenges."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        correct_obj = getattr(challenge, "correct_answer", None)
        if correct_obj is None:
            return Response(
                {"detail": "Correct answer not configured for this challenge."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if correct_obj.case_sensitive:
            is_correct = answer == correct_obj.correct_answer.strip()
        else:
            is_correct = answer.lower() == correct_obj.correct_answer.strip().lower()

        hint_used = bool(request.data.get("hint_used", False))
        if is_correct:
            earned = round(challenge.points * 0.5) if hint_used else challenge.points
        else:
            earned = 0

        Submission.objects.create(
            user=request.user,
            challenge=challenge,
            attempt_no=self._next_attempt_no(request.user, challenge),
            answer_text=answer,
            status="passed" if is_correct else "failed",
            score=earned,
            hint_used=hint_used,
            graded_at=timezone.now(),
        )
        cert, score_changed = check_and_issue_certificate(request.user, challenge.topic.course) if is_correct else (None, False)
        if cert and score_changed:
            _trigger_grade_passback(request.user, challenge.topic.course, cert.score_pct / 100)
        return Response({"correct": is_correct, "score": earned, "certificate_issued": cert is not None})

    # ── Code execution ──────────────────────────────────────────────────────
    def _grade_code(self, request, challenge):
        code = request.data.get("code", "").strip()
        if not code:
            return Response(
                {"detail": "Field 'code' is required for code challenges."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        config = getattr(challenge, "code_config", None)
        if config is None:
            return Response(
                {"detail": "Code config not set for this challenge."},
                status=status.HTTP_404_NOT_FOUND,
            )

        language = request.data.get("language", config.language)
        test_cases = list(config.test_cases.all())

        if not test_cases:
            return Response(
                {"detail": "No test cases configured for this challenge."},
                status=status.HTTP_404_NOT_FOUND,
            )

        submission = Submission.objects.create(
            user=request.user,
            challenge=challenge,
            attempt_no=self._next_attempt_no(request.user, challenge),
            answer_text=code,
            status="pending",
        )

        results = run_code_challenge(
            code,
            language,
            test_cases,
            time_limit_s=config.time_limit_seconds,
            memory_mb=config.memory_limit_mb,
        )

        total_weight = sum(tc.weight for tc in test_cases)
        earned_weight = 0
        passed = 0

        for r in results:
            CodeSubmissionResult.objects.create(
                submission=submission,
                test_case_id=r.test_case_id,
                status=r.status,
                stdout=r.stdout,
                stderr=r.stderr,
                execution_time_ms=r.time_ms,
            )
            if r.status == "accepted":
                passed += 1
                tc = next(tc for tc in test_cases if tc.id == r.test_case_id)
                earned_weight += tc.weight

        hint_used = bool(request.data.get("hint_used", False))
        all_passed = passed == len(results)
        score = round((earned_weight / total_weight) * challenge.points) if total_weight else 0
        if hint_used and all_passed:
            score = round(score * 0.5)

        submission.status = "passed" if all_passed else "failed"
        submission.score = score
        submission.hint_used = hint_used
        submission.feedback = f"{passed}/{len(results)} test cases passed."
        submission.graded_at = timezone.now()
        submission.save()

        cert, score_changed = check_and_issue_certificate(request.user, challenge.topic.course) if all_passed else (None, False)
        if cert and score_changed:
            _trigger_grade_passback(request.user, challenge.topic.course, cert.score_pct / 100)

        return Response({
            "submission_id": submission.id,
            "status": "accepted" if all_passed else "wrong_answer",
            "score": score,
            "passed": passed,
            "total": len(results),
            "certificate_issued": cert is not None,
            "results": [
                {
                    "status": r.status,
                    "time_ms": r.time_ms,
                    "stdout": r.stdout if r.is_public else None,
                    "stderr": r.stderr if r.is_public else None,
                }
                for r in results
            ],
        })


class RevealSolutionView(APIView):
    """
    Reveals the teacher-provided solution explanation for a challenge.
    - Returns 403 if the challenge has no solution explanation.
    - Records the reveal in the database so the student cannot submit anymore.
    - Idempotent: if already revealed, returns the explanation again.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified]

    @swagger_auto_schema(
        tags=["Challenge"],
        operation_summary="Reveal the solution explanation for a challenge",
        operation_description=(
            "Returns the teacher's solution explanation text for the given challenge.\n\n"
            "**Important side-effects:**\n"
            "- If the student has **not yet passed** the challenge, a sentinel `Submission` record "
            "is created with `answer_text='__solution_revealed__'`. This permanently blocks "
            "future submissions for this challenge.\n"
            "- If the student has already passed, the explanation is returned without any side-effects.\n\n"
            "**Idempotent** — calling again after the reveal just returns the explanation again "
            "without creating additional records.\n\n"
            "Returns `403` if the challenge has no solution explanation configured."
        ),
        manual_parameters=[
            openapi.Parameter(
                "slug", openapi.IN_PATH, type=openapi.TYPE_STRING,
                description="Challenge slug", required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Solution explanation text",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "solution_explanation": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                    example={"solution_explanation": "Use a hash map to track seen values. Time complexity: O(n)."},
                ),
            ),
            401: openapi.Response(description="Not authenticated"),
            403: openapi.Response(description="No solution explanation configured for this challenge"),
            404: openapi.Response(description="Challenge not found"),
        },
    )
    def post(self, request, slug):
        challenge = get_object_or_404(
            Challenge.objects.select_related("topic__course"),
            slug=slug,
        )

        if not challenge.solution_explanation:
            return Response(
                {"detail": "No solution explanation is available for this challenge."},
                status=status.HTTP_403_FORBIDDEN,
            )

        _ensure_enrolled(request.user, challenge.topic.course)

        # Check if already passed — still show the explanation but don't mark
        already_passed = Submission.objects.filter(
            user=request.user, challenge=challenge, status="passed"
        ).exists()

        if not already_passed:
            # Mark as solution_revealed — creates/updates a special submission record
            existing_reveal = Submission.objects.filter(
                user=request.user, challenge=challenge, solution_revealed=True
            ).first()
            if not existing_reveal:
                Submission.objects.create(
                    user=request.user,
                    challenge=challenge,
                    attempt_no=self._next_attempt_no(request.user, challenge),
                    answer_text="__solution_revealed__",
                    status="failed",
                    score=0,
                    solution_revealed=True,
                    graded_at=timezone.now(),
                )

        return Response({"solution_explanation": challenge.solution_explanation})

    def _next_attempt_no(self, user, challenge):
        last = (
            Submission.objects.filter(user=user, challenge=challenge)
            .order_by("-attempt_no")
            .values_list("attempt_no", flat=True)
            .first()
        )
        return (last or 0) + 1


class UseHintView(APIView):
    """
    Records that the student has used the hint for a challenge.
    Returns the hint text. Subsequent submissions will receive 50% of points.
    Idempotent: calling again just returns the hint again.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified]

    @swagger_auto_schema(
        tags=["Challenge"],
        operation_summary="Use the hint for a challenge (50% score penalty)",
        operation_description=(
            "Returns the hint text for a challenge and marks the student as having used it.\n\n"
            "**Score penalty:** any subsequent correct submission for this challenge will earn "
            "**50% of the normal points** (`round(points * 0.5)`).\n\n"
            "**Idempotent** — calling again just returns the hint again without creating "
            "additional records or changing the penalty.\n\n"
            "A sentinel `Submission` record with `answer_text='__hint_used__'` is created on first use. "
            "This record is excluded from all stats and status queries.\n\n"
            "Returns `403` if the challenge has no hint configured."
        ),
        manual_parameters=[
            openapi.Parameter(
                "slug", openapi.IN_PATH, type=openapi.TYPE_STRING,
                description="Challenge slug", required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Hint text",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "hint": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                    example={"hint": "Think about which data structure gives O(1) average lookup."},
                ),
            ),
            401: openapi.Response(description="Not authenticated"),
            403: openapi.Response(description="No hint configured for this challenge"),
            404: openapi.Response(description="Challenge not found"),
        },
    )
    def post(self, request, slug):
        challenge = get_object_or_404(
            Challenge.objects.select_related("topic__course"),
            slug=slug,
        )

        if not challenge.hint:
            return Response(
                {"detail": "No hint is available for this challenge."},
                status=status.HTTP_403_FORBIDDEN,
            )

        _ensure_enrolled(request.user, challenge.topic.course)

        # Already used hint?
        already_used = Submission.objects.filter(
            user=request.user, challenge=challenge, hint_used=True
        ).exists()
        if not already_used:
            Submission.objects.create(
                user=request.user,
                challenge=challenge,
                attempt_no=self._next_attempt_no(request.user, challenge),
                answer_text="__hint_used__",
                status="failed",
                score=0,
                hint_used=True,
                graded_at=timezone.now(),
            )

        return Response({"hint": challenge.hint})

    def _next_attempt_no(self, user, challenge):
        last = (
            Submission.objects.filter(user=user, challenge=challenge)
            .order_by("-attempt_no")
            .values_list("attempt_no", flat=True)
            .first()
        )
        return (last or 0) + 1
