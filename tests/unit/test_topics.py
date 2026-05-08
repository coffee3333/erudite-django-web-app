"""Tests for topic create, update, delete and items endpoint."""
import pytest
from core.models.topic_model import Topic
from core.models.lesson import Lesson


CREATE_URL = "/api/platform/topics/create/"


@pytest.fixture
def lesson(topic, teacher):
    return Lesson.objects.create(
        topic=topic,
        title="Lesson One",
        owner=teacher,
        sort_order=1,
    )


@pytest.mark.django_db
class TestTopicCreate:

    def test_create_topic_teacher_owner(self, teacher_client, published_course):
        res = teacher_client.post(CREATE_URL, {
            "title": "New Topic",
            "course_slug": published_course.slug,
        }, format="multipart")
        assert res.status_code == 201
        assert res.data["title"] == "New Topic"

    def test_create_topic_student_forbidden(self, student_client, published_course):
        res = student_client.post(CREATE_URL, {
            "title": "Sneaky Topic",
            "course_slug": published_course.slug,
        }, format="multipart")
        assert res.status_code == 403

    def test_create_topic_unauthenticated(self, api_client, published_course):
        res = api_client.post(CREATE_URL, {
            "title": "Anon Topic",
            "course_slug": published_course.slug,
        }, format="multipart")
        assert res.status_code == 401

    def test_create_topic_missing_course_slug(self, teacher_client):
        res = teacher_client.post(CREATE_URL, {"title": "No Course"}, format="multipart")
        assert res.status_code == 400


@pytest.mark.django_db
class TestTopicUpdate:

    def test_update_topic_title(self, teacher_client, topic):
        url = f"/api/platform/topics/{topic.slug}/update/"
        res = teacher_client.patch(url, {"title": "Renamed Topic"}, format="multipart")
        assert res.status_code == 200
        topic.refresh_from_db()
        assert topic.title == "Renamed Topic"

    def test_update_topic_missing_title(self, teacher_client, topic):
        url = f"/api/platform/topics/{topic.slug}/update/"
        res = teacher_client.patch(url, {}, format="multipart")
        assert res.status_code == 400


@pytest.mark.django_db
class TestTopicDelete:

    def test_delete_topic_by_owner(self, teacher_client, topic):
        url = f"/api/platform/topics/{topic.slug}/delete/"
        res = teacher_client.delete(url)
        assert res.status_code == 204
        assert not Topic.objects.filter(pk=topic.pk).exists()

    def test_delete_topic_by_non_owner(self, teacher2_client, topic):
        url = f"/api/platform/topics/{topic.slug}/delete/"
        res = teacher2_client.delete(url)
        assert res.status_code in (403, 404)


@pytest.mark.django_db
class TestTopicItems:

    def test_topic_items_returns_curriculum(self, student_client, topic, quiz_challenge, lesson):
        url = f"/api/platform/topics/{topic.slug}/items/"
        res = student_client.get(url)
        assert res.status_code == 200
        assert "items" in res.data
        item_types = {item["type"] for item in res.data["items"]}
        assert "lesson" in item_types
        assert "challenge" in item_types

    def test_topic_items_empty_topic(self, student_client, topic):
        url = f"/api/platform/topics/{topic.slug}/items/"
        res = student_client.get(url)
        assert res.status_code == 200
        assert "items" in res.data
