from rest_framework import serializers
from core.models.enrollment_model import CourseEnrollment


class EnrolledStudentSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="student.username")
    enrolled_at = serializers.DateTimeField(format="iso-8601", read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = ["username", "enrolled_at", "lti_source"]
