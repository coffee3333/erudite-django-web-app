"""Tests for challenge submission, grading, hint, and solution reveal."""
import pytest

from core.models.submission_model import Submission
from core.models.challenge_model import Challenge
from core.models.challenge_correct_answer import ChallengeCorrectAnswer
from core.models.challenge_option import ChallengeOption


@pytest.mark.django_db
class TestChallengeList:
    def url(self, topic_slug):
        return f"/api/platform/topics/{topic_slug}/challenges/"

    def test_challenges_listed_for_authenticated_student(
        self, student_client, topic, quiz_challenge
    ):
        res = student_client.get(self.url(topic.slug))
        assert res.status_code == 200
        assert any(c["slug"] == quiz_challenge.slug for c in res.data)

    def test_challenges_listed_anonymously(self, api_client, topic, quiz_challenge):
        res = api_client.get(self.url(topic.slug))
        assert res.status_code == 200

    def test_user_status_is_none_for_anonymous(self, api_client, topic, quiz_challenge):
        res = api_client.get(self.url(topic.slug))
        challenge = next(c for c in res.data if c["slug"] == quiz_challenge.slug)
        assert challenge["user_status"] is None

    def test_user_status_shows_passed(self, student_client, student, topic, quiz_challenge):
        Submission.objects.create(
            user=student, challenge=quiz_challenge,
            attempt_no=1, answer_text="4", status="passed", score=10,
        )
        res = student_client.get(self.url(topic.slug))
        challenge = next(c for c in res.data if c["slug"] == quiz_challenge.slug)
        assert challenge["user_status"] == "passed"

    def test_sentinel_hint_shows_as_failed(
        self, student_client, student, topic, quiz_challenge
    ):
        # Hint sentinel has status="failed" — serializer counts it as such
        Submission.objects.create(
            user=student, challenge=quiz_challenge,
            attempt_no=1, answer_text="__hint_used__",
            status="failed", score=0, hint_used=True,
        )
        res = student_client.get(self.url(topic.slug))
        challenge = next(c for c in res.data if c["slug"] == quiz_challenge.slug)
        assert challenge["user_status"] == "failed"

    def test_hint_available_flag(self, student_client, topic, challenge_with_hint):
        res = student_client.get(self.url(topic.slug))
        challenge = next(c for c in res.data if c["slug"] == challenge_with_hint.slug)
        assert challenge["hint_available"] is True

    def test_solution_text_returned_to_student(
        self, student_client, topic, challenge_with_solution
    ):
        # Serializer returns solution_explanation to all users (gating is in reveal-solution endpoint)
        res = student_client.get(self.url(topic.slug))
        challenge = next(
            c for c in res.data if c["slug"] == challenge_with_solution.slug
        )
        assert challenge["solution_explanation"] == challenge_with_solution.solution_explanation

    def test_owner_receives_hint_and_solution_text(
        self, teacher_client, topic, challenge_with_hint, challenge_with_solution
    ):
        res = teacher_client.get(self.url(topic.slug))
        hint_ch = next(
            c for c in res.data if c["slug"] == challenge_with_hint.slug
        )
        sol_ch = next(
            c for c in res.data if c["slug"] == challenge_with_solution.slug
        )
        assert hint_ch["hint"] == challenge_with_hint.hint
        assert sol_ch["solution_explanation"] == challenge_with_solution.solution_explanation


@pytest.mark.django_db
class TestSubmitQuiz:
    def url(self, slug):
        return f"/api/platform/challenges/{slug}/submit/"

    def test_correct_quiz_answer(self, student_client, quiz_challenge):
        # get the correct option id
        correct_opt = ChallengeOption.objects.get(
            challenge=quiz_challenge, text="4"
        )
        res = student_client.post(self.url(quiz_challenge.slug), {
            "option_id": correct_opt.id,
        }, format="json")
        assert res.status_code == 200
        assert res.data["correct"] is True
        assert res.data["score"] == quiz_challenge.points

    def test_wrong_quiz_answer(self, student_client, quiz_challenge):
        wrong_opt = ChallengeOption.objects.get(
            challenge=quiz_challenge, text="3"
        )
        res = student_client.post(self.url(quiz_challenge.slug), {
            "option_id": wrong_opt.id,
        }, format="json")
        assert res.status_code == 200
        assert res.data["correct"] is False
        assert res.data["score"] == 0

    def test_correct_quiz_with_hint_gives_half_points(
        self, student_client, quiz_challenge
    ):
        correct_opt = ChallengeOption.objects.get(
            challenge=quiz_challenge, text="4"
        )
        res = student_client.post(self.url(quiz_challenge.slug), {
            "option_id": correct_opt.id,
            "hint_used": True,
        }, format="json")
        assert res.status_code == 200
        assert res.data["correct"] is True
        assert res.data["score"] == quiz_challenge.points // 2

    def test_requires_auth(self, api_client, quiz_challenge):
        res = api_client.post(self.url(quiz_challenge.slug), {}, format="json")
        assert res.status_code == 401

    def test_unverified_email_blocked(self, unverified_client, quiz_challenge):
        res = unverified_client.post(self.url(quiz_challenge.slug), {}, format="json")
        assert res.status_code == 403

    def test_missing_option_id_returns_400(self, student_client, quiz_challenge):
        res = student_client.post(self.url(quiz_challenge.slug), {}, format="json")
        assert res.status_code == 400

    def test_invalid_option_id_returns_404(self, student_client, quiz_challenge):
        res = student_client.post(self.url(quiz_challenge.slug), {
            "option_id": 99999,
        }, format="json")
        assert res.status_code == 404

    def test_submission_record_created(self, student_client, student, quiz_challenge):
        correct_opt = ChallengeOption.objects.get(
            challenge=quiz_challenge, text="4"
        )
        student_client.post(self.url(quiz_challenge.slug), {
            "option_id": correct_opt.id,
        }, format="json")
        assert Submission.objects.filter(user=student, challenge=quiz_challenge).exists()

    def test_blocked_after_solution_revealed(
        self, student_client, student, quiz_challenge
    ):
        quiz_challenge.solution_explanation = "The answer is 4."
        quiz_challenge.save()
        Submission.objects.create(
            user=student, challenge=quiz_challenge,
            attempt_no=1, answer_text="__solution_revealed__",
            status="failed", score=0, solution_revealed=True,
        )
        correct_opt = ChallengeOption.objects.get(challenge=quiz_challenge, text="4")
        res = student_client.post(self.url(quiz_challenge.slug), {
            "option_id": correct_opt.id,
        }, format="json")
        assert res.status_code == 403


@pytest.mark.django_db
class TestSubmitText:
    def url(self, slug):
        return f"/api/platform/challenges/{slug}/submit/"

    def test_correct_text_answer(self, student_client, text_challenge):
        res = student_client.post(self.url(text_challenge.slug), {
            "answer": "Paris",
        }, format="json")
        assert res.status_code == 200
        assert res.data["correct"] is True
        assert res.data["score"] == text_challenge.points

    def test_correct_text_case_insensitive(self, student_client, text_challenge):
        res = student_client.post(self.url(text_challenge.slug), {
            "answer": "paris",
        }, format="json")
        assert res.status_code == 200
        assert res.data["correct"] is True

    def test_wrong_text_answer(self, student_client, text_challenge):
        res = student_client.post(self.url(text_challenge.slug), {
            "answer": "London",
        }, format="json")
        assert res.status_code == 200
        assert res.data["correct"] is False
        assert res.data["score"] == 0

    def test_correct_with_hint_gives_half_points(
        self, student_client, text_challenge
    ):
        res = student_client.post(self.url(text_challenge.slug), {
            "answer": "Paris",
            "hint_used": True,
        }, format="json")
        assert res.status_code == 200
        assert res.data["correct"] is True
        assert res.data["score"] == text_challenge.points // 2

    def test_empty_answer_returns_400(self, student_client, text_challenge):
        res = student_client.post(self.url(text_challenge.slug), {
            "answer": "",
        }, format="json")
        assert res.status_code == 400

    def test_blocked_after_solution_revealed(
        self, student_client, student, text_challenge
    ):
        text_challenge.solution_explanation = "Paris is the capital of France."
        text_challenge.save()
        Submission.objects.create(
            user=student, challenge=text_challenge,
            attempt_no=1, answer_text="__solution_revealed__",
            status="failed", score=0, solution_revealed=True,
        )
        res = student_client.post(self.url(text_challenge.slug), {
            "answer": "Paris",
        }, format="json")
        assert res.status_code == 403


@pytest.mark.django_db
class TestUseHint:
    def url(self, slug):
        return f"/api/platform/challenges/{slug}/use-hint/"

    def test_returns_hint_text(self, student_client, challenge_with_hint):
        res = student_client.post(self.url(challenge_with_hint.slug))
        assert res.status_code == 200
        assert res.data["hint"] == challenge_with_hint.hint

    def test_creates_sentinel_submission(
        self, student_client, student, challenge_with_hint
    ):
        # Pre-create a submission so the view has something to flag
        Submission.objects.create(
            user=student, challenge=challenge_with_hint,
            attempt_no=1, answer_text="wrong", status="failed", score=0,
        )
        student_client.post(self.url(challenge_with_hint.slug))
        assert Submission.objects.filter(
            user=student, challenge=challenge_with_hint,
            hint_used=True,
        ).exists()

    def test_idempotent_second_call(self, student_client, student, challenge_with_hint):
        Submission.objects.create(
            user=student, challenge=challenge_with_hint,
            attempt_no=1, answer_text="wrong", status="failed", score=0,
        )
        student_client.post(self.url(challenge_with_hint.slug))
        student_client.post(self.url(challenge_with_hint.slug))
        # hint_used flag set once — still only one submission row
        assert Submission.objects.filter(
            user=student, challenge=challenge_with_hint, hint_used=True
        ).count() == 1

    def test_no_hint_returns_404(self, student_client, quiz_challenge):
        # quiz_challenge has no hint — view returns 404
        res = student_client.post(self.url(quiz_challenge.slug))
        assert res.status_code == 404

    def test_requires_auth(self, api_client, challenge_with_hint):
        res = api_client.post(self.url(challenge_with_hint.slug))
        assert res.status_code == 401

    def test_unverified_email_allowed_for_hints(self, unverified_client, challenge_with_hint):
        # UseHintView only requires IsAuthenticated, not IsEmailVerified
        res = unverified_client.post(self.url(challenge_with_hint.slug))
        assert res.status_code == 200

    def test_user_hint_used_flag_in_challenge_list(
        self, student_client, student, topic, challenge_with_hint
    ):
        # Need a prior submission so the view can flag hint_used on it
        Submission.objects.create(
            user=student, challenge=challenge_with_hint,
            attempt_no=1, answer_text="wrong", status="failed", score=0,
        )
        student_client.post(self.url(challenge_with_hint.slug))
        res = student_client.get(f"/api/platform/topics/{topic.slug}/challenges/")
        ch = next(c for c in res.data if c["slug"] == challenge_with_hint.slug)
        assert ch["user_hint_used"] is True
