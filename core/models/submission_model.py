from django.db import models
from core.models.challenge_model import Challenge
from django.conf import settings

class Submission(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("graded", "Graded"),
        ("rejected", "Rejected"),
    ]

    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="submissions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions"
    )
    attempt_no = models.PositiveIntegerField(default=1)
    answer_text = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    score = models.FloatField(default=0)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("challenge", "user", "attempt_no")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Submission by {self.user.username} for {self.challenge.title}"