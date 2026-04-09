from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404

from authentication.models import User
from core.models.course_model import Course
from core.models.enrollment_model import CourseEnrollment
from core.serializers.enrollment_serializer import EnrolledStudentSerializer


def _get_course_for_owner(slug, request_user):
    """Return course, raise 404/403 if slug not found or user is not owner."""
    course = get_object_or_404(Course, slug=slug)
    if course.owner != request_user and not request_user.is_staff:
        raise PermissionDenied("Only the course owner can manage enrollments.")
    return course


class CourseStudentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, slug):
        """List enrolled students for a private course."""
        course = _get_course_for_owner(slug, request.user)
        enrollments = CourseEnrollment.objects.filter(course=course).select_related("student").order_by("enrolled_at")
        serializer = EnrolledStudentSerializer(enrollments, many=True)
        return Response(serializer.data)

    def post(self, request, slug):
        """Enroll a student by username."""
        course = _get_course_for_owner(slug, request.user)

        username = request.data.get("username", "").strip()
        if not username:
            raise ValidationError({"detail": "Field 'username' is required."})

        try:
            student = User.objects.get(username=username)
        except User.DoesNotExist:
            raise ValidationError({"detail": f"No user with username '{username}' found."})

        if student == request.user:
            raise ValidationError({"detail": "You cannot enroll yourself."})

        enrollment, created = CourseEnrollment.objects.get_or_create(course=course, student=student)
        if not created:
            raise ValidationError({"detail": f"'{username}' is already enrolled."})

        serializer = EnrolledStudentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CourseStudentRemoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, slug, username):
        """Remove an enrolled student by username."""
        course = _get_course_for_owner(slug, request.user)

        try:
            student = User.objects.get(username=username)
        except User.DoesNotExist:
            raise NotFound(f"No user with username '{username}' found.")

        deleted, _ = CourseEnrollment.objects.filter(course=course, student=student).delete()
        if not deleted:
            raise NotFound(f"'{username}' is not enrolled in this course.")

        return Response(status=status.HTTP_204_NO_CONTENT)
