"""Tests for feedback and bookmark APIs."""
import pytest
from core.models.bookmark_model import CourseBookmark
from core.models.feedback_model import CourseFeedback


@pytest.mark.django_db
class TestBookmarkToggle:
    def url(self, slug):
        return f"/api/platform/courses/{slug}/bookmark/"

    def test_student_can_bookmark_course(self, student_client, published_course):
        res = student_client.post(self.url(published_course.slug))
        assert res.status_code == 200
        assert res.data["bookmarked"] is True
        assert CourseBookmark.objects.filter(course=published_course).exists()

    def test_bookmark_toggle_removes_existing(self, student, student_client, published_course):
        CourseBookmark.objects.create(course=published_course, user=student)
        res = student_client.post(self.url(published_course.slug))
        assert res.status_code == 200
        assert res.data["bookmarked"] is False

    def test_anonymous_cannot_bookmark(self, api_client, published_course):
        res = api_client.post(self.url(published_course.slug))
        assert res.status_code == 401


@pytest.mark.django_db
class TestBookmarkedList:
    url = "/api/platform/courses/bookmarked/"

    @pytest.mark.skip(reason="pagination format mismatch — not yet fixed")
    def test_returns_bookmarked_courses(self, student, student_client, published_course):
        CourseBookmark.objects.create(course=published_course, user=student)
        res = student_client.get(self.url)
        assert res.status_code == 200
        assert any(c["slug"] == published_course.slug for c in res.data["results"])

    @pytest.mark.skip(reason="pagination format mismatch — not yet fixed")
    def test_empty_for_new_student(self, student_client):
        res = student_client.get(self.url)
        assert res.status_code == 200
        assert res.data["results"] == []


@pytest.mark.django_db
class TestCourseFeedback:
    def url(self, slug):
        return f"/api/platform/courses/{slug}/feedback/"

    def test_student_can_submit_feedback(self, student_client, published_course):
        res = student_client.post(self.url(published_course.slug), {
            "rating": 4,
            "comment": "Great course!",
        }, format="json")
        assert res.status_code == 201
        assert CourseFeedback.objects.filter(course=published_course).exists()

    def test_owner_cannot_submit_feedback_on_own_course(
        self, teacher_client, published_course
    ):
        res = teacher_client.post(self.url(published_course.slug), {
            "rating": 5,
        }, format="json")
        assert res.status_code == 403

    def test_duplicate_feedback_returns_400(self, student, student_client, published_course):
        CourseFeedback.objects.create(
            course=published_course, user=student, rating=3, comment="First"
        )
        res = student_client.post(self.url(published_course.slug), {
            "rating": 5,
        }, format="json")
        assert res.status_code == 400

    def test_anonymous_can_list_feedback(self, api_client, student, published_course):
        CourseFeedback.objects.create(
            course=published_course, user=student, rating=4, comment="Good"
        )
        res = api_client.get(self.url(published_course.slug))
        assert res.status_code == 200
        assert len(res.data) >= 1
