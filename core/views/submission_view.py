# core/views/submission_view.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsEmailVerified
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.execution.executor import run_code_challenge
from core.models.challenge_model import Challenge
from core.models.challenge_option import ChallengeOption
from core.models.code_challenge import CodeSubmissionResult
from core.models.submission_model import Submission
from core.utils.completion import check_and_issue_certificate
from core.patterns.grader_factory import GraderFactory
from core.views.submission_schemas import submit_schema, reveal_schema, hint_schema


def _ensure_enrolled(user, course):
    if course.status == "private" and course.owner != user:
        from core.models.enrollment_model import CourseEnrollment
        CourseEnrollment.objects.get_or_create(course=course, student=user)


def _trigger_grade_passback(user, course, score_0_to_1: float):
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
        pass


def _next_attempt_no(user, challenge):
    last = (
        Submission.objects.filter(user=user, challenge=challenge)
        .order_by("-attempt_no")
        .values_list("attempt_no", flat=True)
        .first()
    )
    return (last or 0) + 1


def _finalize_and_passback(user, course, is_correct):
    if not is_correct:
        return None
    cert, score_changed = check_and_issue_certificate(user, course)
    if cert and score_changed:
        _trigger_grade_passback(user, course, cert.score_pct / 100)
    return cert


def _check_answer(correct_obj, answer_text):
    correct = correct_obj.correct_answer.strip()
    if correct_obj.case_sensitive:
        return answer_text.strip() == correct
    return answer_text.strip().lower() == correct.lower()


def _calc_earned(points, is_correct, hint_used):
    if not is_correct:
        return 0
    return round(points * 0.5) if hint_used else points


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

    @submit_schema
    def post(self, request, slug):
        challenge = get_object_or_404(
            Challenge.objects.select_related("correct_answer", "code_config", "topic__course"),
            slug=slug,
        )

        _ensure_enrolled(request.user, challenge.topic.course)

        if self._already_revealed(request.user, challenge):
            return Response(
                {"detail": "You have already revealed the solution and cannot submit this challenge anymore."},
                status=status.HTTP_403_FORBIDDEN,
            )

        grader_key = GraderFactory.resolve(challenge.challenge_type, challenge)
        if grader_key == "quiz_mcq":
            return self._grade_quiz(request, challenge)
        if grader_key in ("text", "quiz_text"):
            return self._grade_text(request, challenge)
        if grader_key == "code":
            return self._grade_code(request, challenge)
        return Response(
            {"detail": f"Unknown challenge type: {challenge.challenge_type}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _already_revealed(self, user, challenge):
        if not challenge.solution_explanation:
            return False
        return Submission.objects.filter(
            user=user, challenge=challenge, solution_revealed=True
        ).exists()

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
            return Response({"detail": "Option not found."}, status=status.HTTP_404_NOT_FOUND)

        correct_obj = getattr(challenge, "correct_answer", None)
        if correct_obj is None:
            return Response(
                {"detail": "Correct answer not configured for this challenge."},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_correct = _check_answer(correct_obj, option.text)
        return self._save_and_respond(request, challenge, str(option_id), is_correct)

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

        is_correct = _check_answer(correct_obj, answer)
        return self._save_and_respond(request, challenge, answer, is_correct)

    def _save_and_respond(self, request, challenge, answer_text, is_correct):
        hint_used = bool(request.data.get("hint_used", False))
        earned = _calc_earned(challenge.points, is_correct, hint_used)

        Submission.objects.create(
            user=request.user,
            challenge=challenge,
            attempt_no=_next_attempt_no(request.user, challenge),
            answer_text=answer_text,
            status="passed" if is_correct else "failed",
            score=earned,
            hint_used=hint_used,
            graded_at=timezone.now(),
        )

        cert = _finalize_and_passback(request.user, challenge.topic.course, is_correct)
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

        test_cases = list(config.test_cases.all())
        if not test_cases:
            return Response(
                {"detail": "No test cases configured for this challenge."},
                status=status.HTTP_404_NOT_FOUND,
            )

        language = request.data.get("language", config.language)
        submission = Submission.objects.create(
            user=request.user,
            challenge=challenge,
            attempt_no=_next_attempt_no(request.user, challenge),
            answer_text=code,
            status="pending",
        )

        results = run_code_challenge(
            code, language, test_cases,
            time_limit_s=config.time_limit_seconds,
            memory_mb=config.memory_limit_mb,
        )

        passed, earned_weight = self._save_test_results(submission, results, test_cases)
        all_passed = passed == len(results)
        total_weight = sum(tc.weight for tc in test_cases)
        score = self._calc_code_score(challenge.points, earned_weight, total_weight, all_passed, request.data)

        self._finalize_submission(submission, passed, len(results), all_passed, score, request.data)

        cert = _finalize_and_passback(request.user, challenge.topic.course, all_passed)
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

    def _save_test_results(self, submission, results, test_cases):
        passed = 0
        earned_weight = 0
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
        return passed, earned_weight

    def _calc_code_score(self, points, earned_weight, total_weight, all_passed, data):
        score = round((earned_weight / total_weight) * points) if total_weight else 0
        if all_passed and bool(data.get("hint_used", False)):
            score = round(score * 0.5)
        return score

    def _finalize_submission(self, submission, passed, total, all_passed, score, data):
        submission.status = "passed" if all_passed else "failed"
        submission.score = score
        submission.hint_used = bool(data.get("hint_used", False))
        submission.feedback = f"{passed}/{total} test cases passed."
        submission.graded_at = timezone.now()
        submission.save()


class RevealSolutionView(APIView):
    """
    Reveals the teacher-provided solution explanation for a challenge.
    - Returns 403 if the challenge has no solution explanation.
    - Records the reveal in the database so the student cannot submit anymore.
    - Idempotent: if already revealed, returns the explanation again.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified]

    @reveal_schema
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

        already_passed = Submission.objects.filter(
            user=request.user, challenge=challenge, status="passed"
        ).exists()

        if not already_passed:
            self._record_reveal(request.user, challenge)

        return Response({"solution_explanation": challenge.solution_explanation})

    def _record_reveal(self, user, challenge):
        already_revealed = Submission.objects.filter(
            user=user, challenge=challenge, solution_revealed=True
        ).exists()
        if not already_revealed:
            Submission.objects.create(
                user=user,
                challenge=challenge,
                attempt_no=_next_attempt_no(user, challenge),
                answer_text="__solution_revealed__",
                status="failed",
                score=0,
                solution_revealed=True,
                graded_at=timezone.now(),
            )


class UseHintView(APIView):
    """
    Records that the student has used the hint for a challenge.
    Returns the hint text. Subsequent submissions will receive 50% of points.
    Idempotent: calling again just returns the hint again.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified]

    @hint_schema
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

        already_used = Submission.objects.filter(
            user=request.user, challenge=challenge, hint_used=True
        ).exists()
        if not already_used:
            self._record_hint_used(request.user, challenge)

        return Response({"hint": challenge.hint})

    def _record_hint_used(self, user, challenge):
        Submission.objects.create(
            user=user,
            challenge=challenge,
            attempt_no=_next_attempt_no(user, challenge),
            answer_text="__hint_used__",
            status="failed",
            score=0,
            hint_used=True,
            graded_at=timezone.now(),
        )
