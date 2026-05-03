"""Shared pytest fixtures for all tests."""
import pytest
from rest_framework.test import APIClient

from authentication.models import User
from core.models.course_model import Course
from core.models.topic_model import Topic
from core.models.challenge_model import Challenge
from core.models.challenge_correct_answer import ChallengeCorrectAnswer
from core.models.challenge_option import ChallengeOption
from core.models.submission_model import Submission


# ── Users ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def student(db):
    return User.objects.create_user(
        email="student@test.com",
        username="student",
        password="pass123",
        role="student",
        email_verified=True,
    )


@pytest.fixture
def student2(db):
    return User.objects.create_user(
        email="student2@test.com",
        username="student2",
        password="pass123",
        role="student",
        email_verified=True,
    )


@pytest.fixture
def teacher(db):
    return User.objects.create_user(
        email="teacher@test.com",
        username="teacher",
        password="pass123",
        role="teacher",
        email_verified=True,
    )


@pytest.fixture
def teacher2(db):
    return User.objects.create_user(
        email="teacher2@test.com",
        username="teacher2",
        password="pass123",
        role="teacher",
        email_verified=True,
    )


@pytest.fixture
def unverified_student(db):
    return User.objects.create_user(
        email="unverified@test.com",
        username="unverified",
        password="pass123",
        role="student",
        email_verified=False,
    )


# ── API Clients ────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_client(student):
    client = APIClient()
    client.force_authenticate(user=student)
    return client


@pytest.fixture
def student2_client(student2):
    client = APIClient()
    client.force_authenticate(user=student2)
    return client


@pytest.fixture
def teacher_client(teacher):
    client = APIClient()
    client.force_authenticate(user=teacher)
    return client


@pytest.fixture
def teacher2_client(teacher2):
    client = APIClient()
    client.force_authenticate(user=teacher2)
    return client


@pytest.fixture
def unverified_client(unverified_student):
    client = APIClient()
    client.force_authenticate(user=unverified_student)
    return client


# ── Course / Topic / Challenge hierarchy ──────────────────────────────────────

@pytest.fixture
def published_course(teacher):
    return Course.objects.create(
        owner=teacher,
        title="Published Course",
        description="A public course",
        level="beginner",
        status="published",
    )


@pytest.fixture
def private_course(teacher):
    return Course.objects.create(
        owner=teacher,
        title="Private Course",
        description="A private course",
        level="beginner",
        status="published",
    )


@pytest.fixture
def draft_course(teacher):
    return Course.objects.create(
        owner=teacher,
        title="Draft Course",
        description="A draft course",
        level="beginner",
        status="draft",
    )


@pytest.fixture
def topic(published_course, teacher):
    return Topic.objects.create(
        course=published_course,
        title="Topic One",
        owner=teacher,
    )


@pytest.fixture
def quiz_challenge(topic):
    ch = Challenge.objects.create(
        topic=topic,
        title="Quiz Challenge",
        body="What is 2+2?",
        points=10,
        challenge_type="quiz",
        difficulty="easy",
    )
    opt_a = ChallengeOption.objects.create(challenge=ch, text="3")
    opt_b = ChallengeOption.objects.create(challenge=ch, text="4")
    ChallengeCorrectAnswer.objects.create(
        challenge=ch,
        correct_answer="4",
        case_sensitive=False,
    )
    return ch


@pytest.fixture
def text_challenge(topic):
    ch = Challenge.objects.create(
        topic=topic,
        title="Text Challenge",
        body="What is the capital of France?",
        points=20,
        challenge_type="text",
        difficulty="easy",
    )
    ChallengeCorrectAnswer.objects.create(
        challenge=ch,
        correct_answer="Paris",
        case_sensitive=False,
    )
    return ch


@pytest.fixture
def challenge_with_hint(topic):
    ch = Challenge.objects.create(
        topic=topic,
        title="Hint Challenge",
        body="A tricky question",
        points=20,
        challenge_type="text",
        difficulty="medium",
        hint="Think about France.",
    )
    ChallengeCorrectAnswer.objects.create(
        challenge=ch,
        correct_answer="Paris",
        case_sensitive=False,
    )
    return ch


@pytest.fixture
def challenge_with_solution(topic):
    ch = Challenge.objects.create(
        topic=topic,
        title="Solution Challenge",
        body="Another question",
        points=20,
        challenge_type="text",
        difficulty="medium",
        solution_explanation="The answer is Paris because it is the capital city.",
    )
    ChallengeCorrectAnswer.objects.create(
        challenge=ch,
        correct_answer="Paris",
        case_sensitive=False,
    )
    return ch
