from django.db import models
from django.conf import settings
from .course_model import Course


class CourseBookmark(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="bookmarks")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("course", "user")
