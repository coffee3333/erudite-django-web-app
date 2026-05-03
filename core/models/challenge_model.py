from django.db import models
from core.models.topic_model import Topic
from django.utils.text import slugify


class Challenge(models.Model):
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]
    CHALLENGE_TYPE_CHOICES = [
        ("quiz", "Quiz (MCQ)"),
        ("text", "Text answer"),
        ("code", "Code"),
    ]

    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="challenges"
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    points = models.PositiveIntegerField(default=0)
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_CHOICES, default="medium"
    )
    challenge_type = models.CharField(
        max_length=20, choices=CHALLENGE_TYPE_CHOICES, default="text"
    )
    hint = models.TextField(blank=True, null=True)
    solution_explanation = models.TextField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    photo = models.ImageField(upload_to="challenge_photos/", blank=True, null=True)
    slug = models.SlugField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


    def save(self, *args, **kwargs):
        if not self.title or not self.title.strip():
            raise ValueError("Challenge title cannot be empty.")

        if not self.body or not self.body.strip():
            raise ValueError("Challenge body cannot be empty.")


        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug or "challenge"
            counter = 1
            while Challenge.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)