from django.db import models
from django.conf import settings
from core.models.course_model import Course


class CourseEnrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    lti_source = models.CharField(max_length=200, blank=True, null=True, help_text="LTI platform that created this enrollment, if any.")

    class Meta:
        unique_together = ("course", "student")

    def __str__(self):
        return f"{self.student} → {self.course}"
