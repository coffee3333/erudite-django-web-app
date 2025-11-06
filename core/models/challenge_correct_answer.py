from django.db import models
from core.models.challenge_model import Challenge


class ChallengeCorrectAnswer(models.Model):
    challenge = models.OneToOneField(
        Challenge, on_delete=models.CASCADE, related_name="correct_answer"
    )
    correct_answer = models.CharField(max_length=255)
    case_sensitive = models.BooleanField(default=False)

    def __str__(self):
        return f"Correct answer for {self.challenge.title}"