import uuid
from django.db import models
from django.conf import settings


class Certificate(models.Model):
    user           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    course         = models.ForeignKey("Course", on_delete=models.CASCADE, related_name="certificates")
    certificate_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    issued_at      = models.DateTimeField(auto_now_add=True)
    score_pct      = models.FloatField()

    class Meta:
        unique_together = (("user", "course"),)
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Certificate for {self.user.username} — {self.course.title}"
