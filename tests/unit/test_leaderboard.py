"""Tests for leaderboard ranking and filtering."""
import pytest
from authentication.models import User
from core.models.course_model import Course
from core.models.topic_model import Topic
from core.models.challenge_model import Challenge
from core.models.challenge_correct_answer import ChallengeCorrectAnswer
from core.models.submission_model import Submission


LEADERBOARD_URL = "/api/users/leaderboard/"


def _make_student(i):
    return User.objects.create_user(
        email=f"lb_student{i}@test.com",
        username=f"lb_student{i}",
        password="pass123",
        role="student",
        email_verified=True,
    )


def _make_submission(user, challenge, score, status="passed"):
    return Submission.objects.create(
        user=user,
        challenge=challenge,
        answer_text="Paris",
        status=status,
        score=score,
    )


@pytest.fixture
def lb_challenge(db):
    teacher = User.objects.create_user(
        email="lb_teacher@test.com",
        username="lb_teacher",
        password="pass123",
        role="teacher",
    )
    course = Course.objects.create(
        owner=teacher, title="LB Course", description="x",
        level="beginner", status="published",
    )
    topic = Topic.objects.create(course=course, title="LB Topic", owner=teacher)
    ch = Challenge.objects.create(
        topic=topic, title="LB Challenge", body="Q?",
        points=10, challenge_type="text", difficulty="easy",
    )
    ChallengeCorrectAnswer.objects.create(challenge=ch, correct_answer="Paris", case_sensitive=False)
    return ch


@pytest.mark.django_db
class TestLeaderboardRanking:

    def test_leaderboard_returns_200(self, api_client):
        res = api_client.get(LEADERBOARD_URL)
        assert res.status_code == 200

    def test_leaderboard_has_leaderboard_key(self, api_client):
        res = api_client.get(LEADERBOARD_URL)
        assert "leaderboard" in res.data
        assert isinstance(res.data["leaderboard"], list)

    def test_leaderboard_excludes_teachers(self, api_client, lb_challenge):
        teacher = User.objects.filter(role="teacher").first()
        _make_submission(teacher, lb_challenge, score=100)
        res = api_client.get(LEADERBOARD_URL)
        usernames = [e["username"] for e in res.data["leaderboard"]]
        assert teacher.username not in usernames

    def test_leaderboard_top_10_max(self, api_client, lb_challenge):
        for i in range(12):
            s = _make_student(i)
            _make_submission(s, lb_challenge, score=10 - i if i < 10 else 1)
        res = api_client.get(LEADERBOARD_URL)
        assert len(res.data["leaderboard"]) <= 10

    def test_current_user_outside_top10(self, lb_challenge):
        # Create 11 students with high scores
        for i in range(11):
            s = _make_student(100 + i)
            _make_submission(s, lb_challenge, score=100)
        # Our student has 0 points
        student = _make_student(999)
        client_auth = __import__('rest_framework').test.APIClient()
        client_auth.force_authenticate(user=student)
        res = client_auth.get(LEADERBOARD_URL)
        assert res.status_code == 200
        assert res.data["current_user"] is not None
        assert res.data["current_user"]["username"] == student.username
