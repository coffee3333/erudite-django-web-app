"""Tests for course enrollment management endpoints."""
import pytest
from core.models.enrollment_model import CourseEnrollment


@pytest.mark.django_db
class TestListStudents:

    def test_list_students_by_owner(self, teacher_client, published_course):
        url = f"/api/platform/courses/{published_course.slug}/students/"
        res = teacher_client.get(url)
        assert res.status_code == 200
        assert isinstance(res.data, list)

    def test_list_students_non_owner_forbidden(self, teacher2_client, published_course):
        url = f"/api/platform/courses/{published_course.slug}/students/"
        res = teacher2_client.get(url)
        assert res.status_code == 403

    def test_list_students_unauthenticated(self, api_client, published_course):
        url = f"/api/platform/courses/{published_course.slug}/students/"
        res = api_client.get(url)
        assert res.status_code == 401


@pytest.mark.django_db
class TestEnrollStudent:

    def test_enroll_student(self, teacher_client, published_course, student):
        url = f"/api/platform/courses/{published_course.slug}/students/"
        res = teacher_client.post(url, {"username": student.username}, format="json")
        assert res.status_code == 201
        assert CourseEnrollment.objects.filter(course=published_course, student=student).exists()

    def test_enroll_nonexistent_user(self, teacher_client, published_course):
        url = f"/api/platform/courses/{published_course.slug}/students/"
        res = teacher_client.post(url, {"username": "nobody"}, format="json")
        assert res.status_code == 400

    def test_enroll_already_enrolled(self, teacher_client, published_course, student):
        CourseEnrollment.objects.create(course=published_course, student=student)
        url = f"/api/platform/courses/{published_course.slug}/students/"
        res = teacher_client.post(url, {"username": student.username}, format="json")
        assert res.status_code == 400

    def test_enroll_non_owner_forbidden(self, teacher2_client, published_course, student):
        url = f"/api/platform/courses/{published_course.slug}/students/"
        res = teacher2_client.post(url, {"username": student.username}, format="json")
        assert res.status_code == 403


@pytest.mark.django_db
class TestRemoveStudent:

    def test_remove_enrolled_student(self, teacher_client, published_course, student):
        CourseEnrollment.objects.create(course=published_course, student=student)
        url = f"/api/platform/courses/{published_course.slug}/students/{student.username}/"
        res = teacher_client.delete(url)
        assert res.status_code == 204
        assert not CourseEnrollment.objects.filter(course=published_course, student=student).exists()

    def test_remove_not_enrolled_returns_404(self, teacher_client, published_course, student):
        url = f"/api/platform/courses/{published_course.slug}/students/{student.username}/"
        res = teacher_client.delete(url)
        assert res.status_code == 404

    def test_remove_student_non_owner_forbidden(self, teacher2_client, published_course, student):
        CourseEnrollment.objects.create(course=published_course, student=student)
        url = f"/api/platform/courses/{published_course.slug}/students/{student.username}/"
        res = teacher2_client.delete(url)
        assert res.status_code == 403
