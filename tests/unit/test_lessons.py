"""Tests for lesson create, retrieve, update and delete endpoints."""
import pytest
from core.models.lesson import Lesson


CREATE_URL = "/api/platform/lessons/create/"


@pytest.fixture
def lesson(topic, teacher):
    return Lesson.objects.create(
        topic=topic,
        title="Intro Lesson",
        owner=teacher,
        content="Hello world",
        sort_order=1,
    )


@pytest.mark.django_db
class TestLessonCreate:

    def test_create_lesson_teacher_owner(self, teacher_client, topic):
        res = teacher_client.post(CREATE_URL, {
            "topic_slug": topic.slug,
            "title": "My Lesson",
        }, format="multipart")
        assert res.status_code == 201
        assert res.data["title"] == "My Lesson"

    def test_create_lesson_student_forbidden(self, student_client, topic):
        res = student_client.post(CREATE_URL, {
            "topic_slug": topic.slug,
            "title": "Student Lesson",
        }, format="multipart")
        assert res.status_code == 403

    def test_create_lesson_unauthenticated(self, api_client, topic):
        res = api_client.post(CREATE_URL, {
            "topic_slug": topic.slug,
            "title": "Anon Lesson",
        }, format="multipart")
        assert res.status_code == 401

    def test_create_lesson_missing_topic_slug(self, teacher_client):
        res = teacher_client.post(CREATE_URL, {"title": "No Topic"}, format="multipart")
        assert res.status_code == 400


@pytest.mark.django_db
class TestLessonDetail:

    def test_get_lesson_public(self, api_client, lesson):
        url = f"/api/platform/lessons/{lesson.slug}/"
        res = api_client.get(url)
        assert res.status_code == 200
        assert res.data["title"] == lesson.title

    def test_get_lesson_not_found(self, api_client):
        res = api_client.get("/api/platform/lessons/does-not-exist/")
        assert res.status_code == 404


@pytest.mark.django_db
class TestLessonUpdate:

    def test_update_lesson_by_owner(self, teacher_client, lesson):
        url = f"/api/platform/lessons/{lesson.slug}/update/"
        res = teacher_client.patch(url, {"title": "Updated Lesson"}, format="json")
        assert res.status_code == 200
        lesson.refresh_from_db()
        assert lesson.title == "Updated Lesson"

    def test_update_lesson_by_non_owner(self, student_client, lesson):
        url = f"/api/platform/lessons/{lesson.slug}/update/"
        res = student_client.patch(url, {"title": "Hacked"}, format="json")
        assert res.status_code == 403


@pytest.mark.django_db
class TestLessonDelete:

    def test_delete_lesson_by_owner(self, teacher_client, lesson):
        url = f"/api/platform/lessons/{lesson.slug}/delete/"
        res = teacher_client.delete(url)
        assert res.status_code == 204
        assert not Lesson.objects.filter(pk=lesson.pk).exists()

    def test_delete_lesson_by_non_owner(self, student_client, lesson):
        url = f"/api/platform/lessons/{lesson.slug}/delete/"
        res = student_client.delete(url)
        assert res.status_code == 403
