from django.db import models
from core.models.challenge_model import Challenge
from django.utils.text import slugify


class ChallengeOption(models.Model):
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="options"
    )
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text