"""Tests for private course enrollment management."""
import pytest

from core.models.enrollment_model import CourseEnrollment


@pytest.mark.django_db
class TestEnrollmentList:
    def url(self, slug):
        return f"/api/platform/courses/{slug}/students/"

    def test_owner_can_list_students(self, teacher_client, private_course, student):
        CourseEnrollment.objects.create(course=private_course, student=student)
        res = teacher_client.get(self.url(private_course.slug))
        assert res.status_code == 200
        usernames = [s["username"] for s in res.data]
        assert student.username in usernames

    def test_non_owner_cannot_list_students(self, teacher2_client, private_course):
        res = teacher2_client.get(self.url(private_course.slug))
        assert res.status_code == 403

    def test_student_cannot_list_students(self, student_client, private_course):
        res = student_client.get(self.url(private_course.slug))
        assert res.status_code == 403

    def test_anonymous_cannot_list_students(self, api_client, private_course):
        res = api_client.get(self.url(private_course.slug))
        assert res.status_code == 401

    def test_empty_list_when_no_students(self, teacher_client, private_course):
        res = teacher_client.get(self.url(private_course.slug))
        assert res.status_code == 200
        assert res.data == []


@pytest.mark.django_db
class TestEnrollmentAdd:
    def url(self, slug):
        return f"/api/platform/courses/{slug}/students/"

    def test_owner_can_enroll_student_by_username(
        self, teacher_client, private_course, student
    ):
        res = teacher_client.post(self.url(private_course.slug), {
            "username": student.username,
        }, format="json")
        assert res.status_code == 201
        assert CourseEnrollment.objects.filter(
            course=private_course, student=student
        ).exists()

    def test_cannot_enroll_nonexistent_username(self, teacher_client, private_course):
        res = teacher_client.post(self.url(private_course.slug), {
            "username": "ghost_user_xyz",
        }, format="json")
        assert res.status_code == 404

    def test_cannot_enroll_twice(self, teacher_client, private_course, student):
        teacher_client.post(self.url(private_course.slug), {
            "username": student.username,
        }, format="json")
        res = teacher_client.post(self.url(private_course.slug), {
            "username": student.username,
        }, format="json")
        assert res.status_code == 400
        assert CourseEnrollment.objects.filter(
            course=private_course, student=student
        ).count() == 1

    def test_non_owner_cannot_enroll(
        self, teacher2_client, private_course, student
    ):
        res = teacher2_client.post(self.url(private_course.slug), {
            "username": student.username,
        }, format="json")
        assert res.status_code == 403

    def test_student_cannot_enroll_others(
        self, student_client, private_course, student2
    ):
        res = student_client.post(self.url(private_course.slug), {
            "username": student2.username,
        }, format="json")
        assert res.status_code == 403

    def test_missing_username_returns_400(self, teacher_client, private_course):
        res = teacher_client.post(self.url(private_course.slug), {}, format="json")
        assert res.status_code == 400


@pytest.mark.django_db
class TestEnrollmentRemove:
    def url(self, slug, username):
        return f"/api/platform/courses/{slug}/students/{username}/"

    def test_owner_can_remove_student(
        self, teacher_client, private_course, student
    ):
        CourseEnrollment.objects.create(course=private_course, student=student)
        res = teacher_client.delete(self.url(private_course.slug, student.username))
        assert res.status_code == 204
        assert not CourseEnrollment.objects.filter(
            course=private_course, student=student
        ).exists()

    def test_remove_nonexistent_student_returns_404(
        self, teacher_client, private_course, student
    ):
        res = teacher_client.delete(self.url(private_course.slug, student.username))
        assert res.status_code == 404

    def test_non_owner_cannot_remove(
        self, teacher2_client, private_course, student
    ):
        CourseEnrollment.objects.create(course=private_course, student=student)
        res = teacher2_client.delete(self.url(private_course.slug, student.username))
        assert res.status_code == 403

    def test_student_cannot_remove_others(
        self, student_client, private_course, student2
    ):
        CourseEnrollment.objects.create(course=private_course, student=student2)
        res = student_client.delete(self.url(private_course.slug, student2.username))
        assert res.status_code == 403

    def test_removed_student_loses_access(
        self, student_client, student, private_course, teacher_client
    ):
        CourseEnrollment.objects.create(course=private_course, student=student)
        # Confirm access exists
        res = student_client.get(f"/api/platform/courses/{private_course.slug}/")
        assert res.status_code == 200
        # Remove
        teacher_client.delete(
            f"/api/platform/courses/{private_course.slug}/students/{student.username}/"
        )
        # Access should be gone
        res = student_client.get(f"/api/platform/courses/{private_course.slug}/")
        assert res.status_code == 404
